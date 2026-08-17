"""The null-space coverage test — the gate that decides what may be recovered.

This module implements the single most important check in the package, and the
reason the package exists.

Model the observation as ``y = Ax + n``. When ``A`` is a blur or downsampling
operator it attenuates information but does not destroy it, and regularised
inversion recovers ``x`` up to the noise floor with a computable error bound.
When ``A`` is a *masking* operator it is a projection: it annihilates a
subspace. The data then constrains nothing whatsoever about the component of
``x`` lying in ``ker(A)``. Infinitely many images satisfy the measurement
exactly and equally well, and no amount of computation distinguishes between
them, because the distinguishing information is not attenuated — it is absent.

The standard escape route is compressed sensing, which does recover null-space
content, but only when the signal is sparse in some basis *and* the measurement
operator satisfies a restricted isometry property. A contiguous physical
occluder is the worst case for RIP: the loss is spatially coherent and highly
structured rather than incoherent and spread, so the recovery guarantees do not
apply. This is not a limitation of any particular algorithm.

There is exactly one honest way out, and this module measures whether it is
available: if the occluder *moves relative to the scene* across frames, then
different frames annihilate different subspaces, and the union of what they
observe may cover the whole. Where the union covers a pixel, recovery is a
measurement. Where it does not, any value written there is invention.

``coverage_report`` computes that union per pixel. ``recovery`` refuses to write
anywhere it reports zero.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import ndimage

from .registration import Shift

__all__ = ["CoverageReport", "coverage_report", "warp_visibility"]


def warp_visibility(visible: np.ndarray, shift: Shift) -> np.ndarray:
    """Bring a frame's visibility mask into reference coordinates.

    Nearest-neighbour resampling (order=0) is deliberate: interpolating a
    boolean mask produces fractional visibility, which invites treating a pixel
    that is 30% observed as observed. A pixel is either measured or it is not.
    """
    warped = ndimage.shift(
        visible.astype(np.float64),
        shift=(-shift.dy, -shift.dx),
        order=0,
        mode="constant",
        cval=0.0,
        prefilter=False,
    )
    return warped > 0.5


@dataclass
class CoverageReport:
    """Per-pixel count of how many frames observed each location."""

    counts: np.ndarray  # int, shape == reference frame shape
    n_frames: int

    @property
    def covered(self) -> np.ndarray:
        """Pixels observed at least once — the recoverable support."""
        return self.counts > 0

    @property
    def null_space(self) -> np.ndarray:
        """Pixels observed by no frame. Unconstrained by the data. Never fill."""
        return self.counts == 0

    @property
    def null_space_fraction(self) -> float:
        return float(np.mean(self.null_space))

    @property
    def coverage_fraction(self) -> float:
        return float(np.mean(self.covered))

    @property
    def mean_multiplicity(self) -> float:
        """Average observations per covered pixel.

        Above ~2 there is genuine redundancy to exploit for noise reduction and
        sub-pixel detail. At exactly 1 the pixel is recoverable but not
        improvable, and its noise is whatever the single contributing frame had.
        """
        c = self.counts[self.covered]
        return float(np.mean(c)) if c.size else 0.0

    def largest_hole_px(self) -> int:
        """Size of the biggest contiguous unobserved region.

        Scattered single-pixel holes and one large connected hole have very
        different meanings even at identical null-space fractions: the former
        may be interpolable under a smoothness assumption that is defensible at
        one-pixel scale, the latter never is.
        """
        labels, n = ndimage.label(self.null_space)
        if n == 0:
            return 0
        sizes = ndimage.sum_labels(
            np.ones_like(labels), labels, index=np.arange(1, n + 1)
        )
        return int(sizes.max())

    def summary(self) -> dict[str, object]:
        return {
            "n_frames": self.n_frames,
            "coverage_fraction": self.coverage_fraction,
            "null_space_fraction": self.null_space_fraction,
            "mean_multiplicity": self.mean_multiplicity,
            "largest_hole_px": self.largest_hole_px(),
            "recoverable": bool(self.covered.any()),
            "fully_covered": bool(not self.null_space.any()),
        }


def coverage_report(
    visibility_masks: list[np.ndarray],
    shifts: list[Shift],
) -> CoverageReport:
    """Accumulate per-pixel observation counts across a registered frame stack.

    ``visibility_masks[i]`` is True where frame ``i`` shows the scene (i.e. the
    complement of that frame's occlusion mask). ``shifts[i]`` is that frame's
    registration against the reference.

    The result is the honest answer to "what do we actually have?", and it is
    computed *before* any recovery is attempted so that the answer cannot be
    rationalised after seeing an appealing reconstruction.
    """
    if len(visibility_masks) != len(shifts):
        raise ValueError(
            f"{len(visibility_masks)} masks but {len(shifts)} shifts; "
            "every frame needs a registration"
        )
    if not visibility_masks:
        raise ValueError("empty frame stack")

    shape = visibility_masks[0].shape
    counts = np.zeros(shape, dtype=np.int32)

    for mask, shift in zip(visibility_masks, shifts):
        if mask.shape != shape:
            raise ValueError(f"mask shape {mask.shape} != reference {shape}")
        counts += warp_visibility(mask, shift).astype(np.int32)

    return CoverageReport(counts=counts, n_frames=len(visibility_masks))
