"""Multi-frame recovery, gated on coverage.

Recovery here means one thing only: combining observations that genuinely
exist across a registered frame stack. Where the coverage report says a pixel
was observed, this module reconstructs it and records which frames contributed.
Where coverage says zero, the output is NaN — permanently, by construction, with
no parameter that changes it.

That NaN is the product. It is the difference between an instrument and a
generator: an instrument's output has holes exactly where reality gave it no
data, and an analyst can see them.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .coverage import CoverageReport, warp_visibility
from .registration import Shift, apply_shift

__all__ = ["Recovery", "fuse_visible", "iterative_back_projection"]


@dataclass
class Recovery:
    """A fused estimate together with its support and provenance."""

    image: np.ndarray  # float64; NaN wherever unobserved
    support: np.ndarray  # bool; True where a value was measured
    contributions: np.ndarray  # int; how many frames fed each pixel
    dispersion: np.ndarray  # float; per-pixel std across contributors, NaN if <2

    @property
    def unrecovered(self) -> np.ndarray:
        """Pixels left as NaN. These are not gaps to be filled — they are the result."""
        return ~self.support

    @property
    def unrecovered_fraction(self) -> float:
        return float(np.mean(self.unrecovered))

    def disagreement_flags(self, threshold: float = 0.1) -> np.ndarray:
        """Pixels where contributing frames disagree beyond ``threshold``.

        High dispersion on a multiply-observed pixel means registration error,
        a moving scene element, or an occlusion mask that leaked. All three
        invalidate the fused value, so these are flagged rather than trusted.
        """
        return np.where(np.isnan(self.dispersion), False, self.dispersion > threshold)

    def summary(self) -> dict[str, object]:
        flagged = self.disagreement_flags()
        return {
            "recovered_fraction": float(np.mean(self.support)),
            "unrecovered_fraction": self.unrecovered_fraction,
            "max_contributions": int(self.contributions.max()) if self.contributions.size else 0,
            "disagreement_px": int(flagged.sum()),
        }


def fuse_visible(
    frames: list[np.ndarray],
    visibility_masks: list[np.ndarray],
    shifts: list[Shift],
    coverage: CoverageReport,
) -> Recovery:
    """Fuse the visible parts of a registered stack into one estimate.

    Each frame is resampled into reference coordinates, its occluded pixels are
    discarded, and the surviving samples are averaged per pixel. Averaging is
    the maximum-likelihood combination under independent Gaussian noise, which
    is the right assumption for repeated observations from one sensor and gives
    the familiar sqrt(N) noise reduction where multiplicity allows.

    Pixels with zero coverage are never written. The ``coverage`` argument is
    required rather than recomputed so that the gate and the recovery provably
    refer to the same analysis.
    """
    if not (len(frames) == len(visibility_masks) == len(shifts)):
        raise ValueError("frames, masks and shifts must be the same length")
    if not frames:
        raise ValueError("empty frame stack")

    shape = frames[0].shape
    if coverage.counts.shape != shape:
        raise ValueError(
            f"coverage shape {coverage.counts.shape} != frame shape {shape}; "
            "the coverage report must come from this same stack"
        )

    total = np.zeros(shape, dtype=np.float64)
    total_sq = np.zeros(shape, dtype=np.float64)
    n = np.zeros(shape, dtype=np.int32)

    for frame, mask, shift in zip(frames, visibility_masks, shifts):
        warped = apply_shift(frame, shift)
        warped_vis = warp_visibility(mask, shift)
        # A pixel counts only if it was inside the frame *and* not occluded.
        usable = warped_vis & np.isfinite(warped)
        vals = np.where(usable, warped, 0.0)
        total += vals
        total_sq += vals * vals
        n += usable.astype(np.int32)

    support = n > 0
    with np.errstate(invalid="ignore", divide="ignore"):
        mean = np.where(support, total / np.maximum(n, 1), np.nan)
        # Population variance across contributors; only defined for n >= 2.
        var = np.where(n > 1, total_sq / np.maximum(n, 1) - mean**2, np.nan)
        dispersion = np.sqrt(np.maximum(var, 0.0))

    return Recovery(
        image=mean,
        support=support,
        contributions=n,
        dispersion=dispersion,
    )


def iterative_back_projection(
    recovery: Recovery,
    frames: list[np.ndarray],
    visibility_masks: list[np.ndarray],
    shifts: list[Shift],
    iterations: int = 5,
    step: float = 0.5,
) -> Recovery:
    """Refine a fused estimate by back-projecting its residual against each frame.

    Classical IBP: simulate what each frame *should* have observed given the
    current estimate, take the residual against what it *did* observe, and
    correct. Repeated, this sharpens detail that sub-pixel frame offsets encode
    but simple averaging blurs.

    The correction is applied only on the existing support. IBP cannot create
    support — a residual can only be computed where an observation exists — so
    the null space is untouched by construction, not by a guard we could forget.

    ``step`` under-relaxes the update; values near 1.0 converge faster but
    amplify registration error into ringing.
    """
    if iterations < 0:
        raise ValueError("iterations must be non-negative")
    if not 0.0 < step <= 1.0:
        raise ValueError("step must lie in (0, 1]")

    estimate = np.where(recovery.support, recovery.image, 0.0)
    support = recovery.support

    for _ in range(iterations):
        correction = np.zeros_like(estimate)
        weight = np.zeros_like(estimate)

        for frame, mask, shift in zip(frames, visibility_masks, shifts):
            warped = apply_shift(frame, shift)
            warped_vis = warp_visibility(mask, shift)
            usable = warped_vis & np.isfinite(warped) & support
            residual = np.where(usable, warped - estimate, 0.0)
            correction += residual
            weight += usable.astype(np.float64)

        with np.errstate(invalid="ignore", divide="ignore"):
            update = np.where(weight > 0, correction / np.maximum(weight, 1.0), 0.0)
        estimate = estimate + step * update

    out = np.where(support, estimate, np.nan)
    return Recovery(
        image=out,
        support=support,
        contributions=recovery.contributions,
        dispersion=recovery.dispersion,
    )
