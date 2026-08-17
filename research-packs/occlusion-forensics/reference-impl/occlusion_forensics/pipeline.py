"""End-to-end analysis in the order the argument requires.

The sequence matters and is not merely convenient:

  1. clarity   — where is there detail at all?
  2. occlusion — where is the measurement blocked?
  3. weave     — what is the occluder, as a material?
  4. register  — how do the frames relate?
  5. coverage  — what does the data actually constrain?   <-- the gate
  6. recover   — fuse only what step 5 licensed.

Coverage is computed before recovery so that the decision about what may be
reconstructed is made from the observation geometry alone, and cannot be
revisited after seeing a reconstruction that happens to look convincing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .clarity import ClarityMap, clarity_map
from .coverage import CoverageReport, coverage_report
from .determinism import RunManifest
from .occlusion import OcclusionMask, occlusion_mask
from .recovery import Recovery, fuse_visible, iterative_back_projection
from .registration import Shift, register_stack
from .report import Claim, Determination, Region, Report
from .weave import WeaveDescriptor, analyse_weave

__all__ = ["StackAnalysis", "analyse_stack"]


@dataclass
class StackAnalysis:
    """Everything one run produced, including the intermediates."""

    clarity: list[ClarityMap]
    occlusions: list[OcclusionMask]
    weaves: list[WeaveDescriptor]
    shifts: list[Shift]
    coverage: CoverageReport
    recovery: Recovery | None
    report: Report


def _largest_occluded_region(mask: np.ndarray) -> Region | None:
    """Bounding box of the biggest occluded component, for weave sampling."""
    from scipy import ndimage

    labels, n = ndimage.label(mask)
    if n == 0:
        return None
    sizes = ndimage.sum_labels(np.ones_like(labels), labels, index=np.arange(1, n + 1))
    biggest = int(np.argmax(sizes)) + 1
    # find_objects needs an integer label array; a bool mask raises on scipy>=1.15.
    slices = ndimage.find_objects((labels == biggest).astype(np.int32))
    if not slices or slices[0] is None:
        return None
    sy, sx = slices[0]
    return Region(int(sy.start), int(sy.stop), int(sx.start), int(sx.stop))


def analyse_stack(
    frames: list[np.ndarray],
    *,
    tile: int = 16,
    reference_index: int = 0,
    ibp_iterations: int = 3,
    tool_version: str = "0.1.0",
    parameters: dict[str, Any] | None = None,
) -> StackAnalysis:
    """Run the full deterministic pipeline over a frame stack.

    A single-frame stack is legitimate input and returns a coverage report whose
    null space is exactly that frame's occlusion. That is the common real-world
    case, and its correct output is a large unrecovered region — not a failure,
    and not a prompt to fill it.
    """
    if not frames:
        raise ValueError("empty frame stack")

    manifest = RunManifest(tool_version=tool_version)
    manifest.parameters = {
        "tile": tile,
        "reference_index": reference_index,
        "ibp_iterations": ibp_iterations,
        **(parameters or {}),
    }
    for i, f in enumerate(frames):
        manifest.add_array_input(f"frame_{i:03d}", f)

    rpt = Report(manifest={})
    rpt.log(f"loaded {len(frames)} frame(s), shape {frames[0].shape}")

    clarities = [clarity_map(f, tile=tile) for f in frames]
    rpt.log(
        "clarity: anchor fractions "
        + ", ".join(f"{c.anchor_fraction:.3f}" for c in clarities)
    )

    occlusions = [occlusion_mask(f) for f in frames]
    rpt.log(
        "occlusion: occluded fractions "
        + ", ".join(f"{o.occluded_fraction:.3f}" for o in occlusions)
    )

    weaves: list[WeaveDescriptor] = []
    for f, occ in zip(frames, occlusions):
        region = _largest_occluded_region(occ.mask)
        if region is None or min(region.row1 - region.row0, region.col1 - region.col0) < 8:
            weaves.append(WeaveDescriptor(0.0, 0.0, 0.0, (0.0, 0.0), False))
            continue
        patch = f[region.row0 : region.row1, region.col0 : region.col1]
        w = analyse_weave(patch)
        weaves.append(w)
        if w.detected:
            rpt.add(
                Claim(
                    attribute="occluder_weave_pitch",
                    determination=Determination.MEASURED,
                    method="2D FFT dominant-peak analysis (weave.analyse_weave)",
                    region=region,
                    value=w.pitch_px,
                    # One frequency bin over the region's extent is the
                    # resolution limit of the estimate.
                    uncertainty=w.pitch_px**2 / max(region.row1 - region.row0, 1),
                    units="pixels",
                    note=f"regularity {w.regularity:.1f}x background",
                )
            )

    shifts = register_stack(frames, reference_index=reference_index)
    rpt.log(
        "registration: shifts "
        + ", ".join(f"({s.dy:+.2f},{s.dx:+.2f})" for s in shifts)
    )
    weak = [i for i, s in enumerate(shifts) if s.peak < 0.05]
    if weak:
        rpt.log(f"WARNING: weak registration peak on frames {weak}; shifts unreliable")

    visibility = [o.visible for o in occlusions]
    cov = coverage_report(visibility, shifts)
    rpt.coverage = cov.summary()
    rpt.log(
        f"coverage: {cov.coverage_fraction:.3f} observed, "
        f"{cov.null_space_fraction:.3f} in null space, "
        f"largest hole {cov.largest_hole_px()} px"
    )

    rec: Recovery | None = None
    if cov.covered.any():
        rec = fuse_visible(frames, visibility, shifts, cov)
        if ibp_iterations > 0 and len(frames) > 1:
            rec = iterative_back_projection(
                rec, frames, visibility, shifts, iterations=ibp_iterations
            )
        rpt.log(
            f"recovery: {rec.summary()['recovered_fraction']:.3f} of frame recovered; "
            f"{rec.unrecovered_fraction:.3f} left as NaN"
        )
    else:
        rpt.log("recovery: skipped, coverage is empty")

    if cov.null_space.any():
        rpt.add(
            Claim(
                attribute="null_space_geometry",
                determination=Determination.INSUFFICIENT_DATA,
                method="coverage.coverage_report",
                note=(
                    f"{cov.null_space_fraction:.1%} of the frame was observed by no "
                    f"frame in this stack (largest contiguous hole "
                    f"{cov.largest_hole_px()} px). The data places no constraint on "
                    "these pixels. Additional frames in which the occluder moves "
                    "relative to the scene are the only way to reduce this."
                ),
            )
        )

    # Record the refusals explicitly so the report shows they were considered.
    for attribute in ("identity", "race", "sex", "occluded_facial_geometry"):
        rpt.declare_not_measurable(attribute)

    if rec is not None:
        manifest.add_output("recovered", rec.image)
        manifest.add_output("support", rec.support)
    manifest.add_output("coverage_counts", cov.counts)
    rpt.manifest = {
        **manifest.to_dict(),
        "manifest_hash": manifest.manifest_hash(),
    }

    return StackAnalysis(
        clarity=clarities,
        occlusions=occlusions,
        weaves=weaves,
        shifts=shifts,
        coverage=cov,
        recovery=rec,
        report=rpt,
    )
