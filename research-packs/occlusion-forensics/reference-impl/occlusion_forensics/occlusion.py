"""Occlusion segmentation via structure-tensor coherence.

Woven and knitted fabric has a signature that skin does not: strongly oriented,
locally consistent gradient structure at a fixed pitch. The structure tensor
measures exactly that consistency, so it separates fabric from face without any
learned model, and — critically — without any notion of what a face looks like.

The output is a binary mask marking *where the measurement is blocked*. It says
nothing about what lies behind, and no function in this module attempts to.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import ndimage

__all__ = ["StructureTensor", "structure_tensor", "OcclusionMask", "occlusion_mask"]


@dataclass
class StructureTensor:
    """Eigen-decomposition of the smoothed gradient outer product."""

    coherence: np.ndarray  # [0, 1]; 1 = perfectly oriented, 0 = isotropic
    orientation: np.ndarray  # radians in [0, pi)
    energy: np.ndarray  # trace, i.e. total local gradient power

    @property
    def shape(self) -> tuple[int, ...]:
        return self.coherence.shape


def structure_tensor(image: np.ndarray, sigma: float = 2.0) -> StructureTensor:
    """Compute per-pixel orientation coherence.

    The tensor J = [[Ix^2, IxIy], [IxIy, Iy^2]], Gaussian-smoothed at ``sigma``,
    has eigenvalues l1 >= l2 >= 0. Coherence ((l1 - l2) / (l1 + l2))^2 is 1 for a
    perfectly oriented pattern and 0 where gradients point every which way.

    ``sigma`` sets the neighbourhood over which orientation must agree. It should
    exceed the weave pitch you expect to detect, or the tensor measures the
    orientation of individual threads rather than of the fabric.
    """
    if sigma <= 0:
        raise ValueError("sigma must be positive")

    ix = ndimage.sobel(image, axis=1, mode="reflect")
    iy = ndimage.sobel(image, axis=0, mode="reflect")

    jxx = ndimage.gaussian_filter(ix * ix, sigma, mode="reflect")
    jyy = ndimage.gaussian_filter(iy * iy, sigma, mode="reflect")
    jxy = ndimage.gaussian_filter(ix * iy, sigma, mode="reflect")

    trace = jxx + jyy
    # Closed-form eigenvalue gap for a symmetric 2x2 matrix.
    diff = jxx - jyy
    gap = np.sqrt(diff * diff + 4.0 * jxy * jxy)

    # Guard the flat-region case: where there is no gradient energy there is no
    # orientation to speak of, and coherence is defined as 0 rather than 0/0.
    with np.errstate(divide="ignore", invalid="ignore"):
        coherence = np.where(trace > 0, (gap / trace) ** 2, 0.0)

    orientation = 0.5 * np.arctan2(2.0 * jxy, diff)
    orientation = np.mod(orientation, np.pi)

    return StructureTensor(
        coherence=np.clip(coherence, 0.0, 1.0),
        orientation=orientation,
        energy=trace,
    )


@dataclass
class OcclusionMask:
    """Binary occlusion mask plus the intermediates that produced it."""

    mask: np.ndarray  # bool; True = occluded / measurement blocked
    coherence: np.ndarray
    energy: np.ndarray
    coherence_threshold: float
    energy_threshold: float

    @property
    def occluded_fraction(self) -> float:
        return float(np.mean(self.mask))

    @property
    def visible(self) -> np.ndarray:
        """Complement of the mask — the pixels that carry usable measurement."""
        return ~self.mask


def occlusion_mask(
    image: np.ndarray,
    sigma: float = 2.0,
    coherence_threshold: float = 0.5,
    energy_quantile: float = 0.4,
    min_region_px: int = 64,
) -> OcclusionMask:
    """Segment strongly oriented, textured regions as occluding material.

    Two conditions must both hold: orientation coherence above
    ``coherence_threshold``, and gradient energy above the ``energy_quantile``
    of the frame. The energy condition suppresses flat backgrounds, which are
    technically coherent (any smooth ramp is) but are not fabric.

    Connected components smaller than ``min_region_px`` are discarded. Real
    occluders are contiguous; isolated speckle is noise passing threshold.

    This is a heuristic and is stated as one. It is appropriate for triage —
    deciding which pixels to *exclude* from analysis. Excluding a pixel that was
    actually visible costs coverage; including one that was occluded corrupts a
    measurement. The defaults are therefore tuned to over-exclude.
    """
    st = structure_tensor(image, sigma=sigma)
    energy_threshold = float(np.quantile(st.energy, energy_quantile))

    raw = (st.coherence > coherence_threshold) & (st.energy > energy_threshold)

    labels, n = ndimage.label(raw)
    if n > 0:
        sizes = ndimage.sum_labels(np.ones_like(labels), labels, index=np.arange(1, n + 1))
        keep = np.zeros(n + 1, dtype=bool)
        keep[1:] = sizes >= min_region_px
        mask = keep[labels]
    else:
        mask = raw

    return OcclusionMask(
        mask=mask,
        coherence=st.coherence,
        energy=st.energy,
        coherence_threshold=coherence_threshold,
        energy_threshold=energy_threshold,
    )
