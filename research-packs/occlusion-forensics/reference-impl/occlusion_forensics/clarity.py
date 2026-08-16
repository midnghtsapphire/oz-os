"""Clarity mapping — locating the regions that actually carry detail.

This is the "pixel anchoring" step. Before any reasoning about content, we
measure *where the image is sharp*, tile by tile. Sharp tiles are anchors:
claims may be made about them. Soft tiles are not evidence, and the report must
say so rather than quietly averaging them in.

Three independent focus operators are provided. They disagree in useful ways —
Laplacian variance is sensitive to noise, Tenengrad to edge density, Brenner to
directional structure — so agreement between them is worth more than any one
score. ``clarity_map`` therefore reports each separately instead of collapsing
them into a single number that hides the disagreement.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from scipy import ndimage

__all__ = [
    "FocusMetric",
    "laplacian_variance",
    "tenengrad",
    "brenner",
    "tile_metric",
    "ClarityMap",
    "clarity_map",
]

FocusMetric = Literal["laplacian_variance", "tenengrad", "brenner"]


def laplacian_variance(tile: np.ndarray) -> float:
    """Variance of the Laplacian. High for in-focus, textured content.

    Also high for sensor noise, which is why it is never used alone.
    """
    return float(np.var(ndimage.laplace(tile)))


def tenengrad(tile: np.ndarray) -> float:
    """Mean squared Sobel gradient magnitude — total edge energy."""
    gx = ndimage.sobel(tile, axis=1, mode="reflect")
    gy = ndimage.sobel(tile, axis=0, mode="reflect")
    return float(np.mean(gx * gx + gy * gy))


def brenner(tile: np.ndarray) -> float:
    """Brenner gradient: squared difference at a two-pixel horizontal lag.

    Cheap, and notably robust to the fine-grain noise that inflates Laplacian
    variance, because the two-pixel lag acts as a mild low-pass.
    """
    if tile.shape[1] < 3:
        return 0.0
    d = tile[:, 2:] - tile[:, :-2]
    return float(np.mean(d * d))


_METRICS = {
    "laplacian_variance": laplacian_variance,
    "tenengrad": tenengrad,
    "brenner": brenner,
}


def tile_metric(image: np.ndarray, tile: int, metric: FocusMetric) -> np.ndarray:
    """Apply a focus operator over a non-overlapping tile grid.

    Returns a (H // tile, W // tile) array. Partial tiles at the right and
    bottom edges are dropped rather than padded: a padded tile reports the
    sharpness of the padding, not of the image.
    """
    if tile < 3:
        raise ValueError("tile must be at least 3 px to support the operators")
    fn = _METRICS[metric]
    h, w = image.shape
    nh, nw = h // tile, w // tile
    if nh == 0 or nw == 0:
        raise ValueError(f"tile {tile} exceeds image dimensions {image.shape}")

    out = np.empty((nh, nw), dtype=np.float64)
    for i in range(nh):
        for j in range(nw):
            out[i, j] = fn(image[i * tile : (i + 1) * tile, j * tile : (j + 1) * tile])
    return out


@dataclass
class ClarityMap:
    """Per-tile clarity scores plus the anchor mask derived from them."""

    tile: int
    scores: dict[str, np.ndarray]
    anchor_quantile: float
    anchors: np.ndarray  # bool, shape == scores[*].shape

    @property
    def grid_shape(self) -> tuple[int, int]:
        return self.anchors.shape

    @property
    def anchor_fraction(self) -> float:
        return float(np.mean(self.anchors))

    def tile_bounds(self, i: int, j: int) -> tuple[int, int, int, int]:
        """Pixel bounds (row0, row1, col0, col1) of tile (i, j).

        Reports cite these, so a reader can crop the exact region a claim
        refers to.
        """
        return (i * self.tile, (i + 1) * self.tile, j * self.tile, (j + 1) * self.tile)


def clarity_map(
    image: np.ndarray,
    tile: int = 16,
    anchor_quantile: float = 0.75,
    require_agreement: int = 2,
) -> ClarityMap:
    """Compute all three focus metrics and mark anchor tiles.

    A tile is an anchor when at least ``require_agreement`` of the three metrics
    place it above ``anchor_quantile`` within its own metric's distribution.
    Per-metric quantiles make the threshold scale-free, so the same parameters
    work on a bright daylight frame and a dim IR frame without retuning.
    """
    if not 0.0 < anchor_quantile < 1.0:
        raise ValueError("anchor_quantile must lie strictly between 0 and 1")
    if not 1 <= require_agreement <= 3:
        raise ValueError("require_agreement must be 1, 2 or 3")

    scores: dict[str, np.ndarray] = {}
    votes = None
    for name in _METRICS:
        s = tile_metric(image, tile, name)  # type: ignore[arg-type]
        scores[name] = s
        thresh = float(np.quantile(s, anchor_quantile))
        v = (s > thresh).astype(np.int8)
        votes = v if votes is None else votes + v

    assert votes is not None
    anchors = votes >= require_agreement
    return ClarityMap(
        tile=tile,
        scores=scores,
        anchor_quantile=anchor_quantile,
        anchors=anchors,
    )
