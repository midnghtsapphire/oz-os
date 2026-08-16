"""Image loading with a documented, lossless-to-float conversion path.

Everything downstream operates on float64 luminance in [0, 1]. Converting once,
here, keeps the colour-science assumption in a single auditable place instead of
scattering ad-hoc ``mean(axis=2)`` calls through the analysis modules.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

__all__ = ["REC709_WEIGHTS", "to_luminance", "load_luminance", "load_stack"]

# Rec.709 luma coefficients. These describe how a *display-referred* sRGB
# encoding maps to perceived brightness. They are not a statement about scene
# radiance and carry no information about surface reflectance or material.
REC709_WEIGHTS = (0.2126, 0.7152, 0.0722)


def to_luminance(rgb: np.ndarray) -> np.ndarray:
    """Convert an HxWx3 (or HxWx4, or HxW) array to float64 luminance in [0, 1]."""
    arr = np.asarray(rgb)
    if arr.dtype == np.uint8:
        arr = arr.astype(np.float64) / 255.0
    elif arr.dtype == np.uint16:
        arr = arr.astype(np.float64) / 65535.0
    else:
        arr = arr.astype(np.float64)

    if arr.ndim == 2:
        lum = arr
    elif arr.ndim == 3:
        # Drop any alpha channel; alpha is compositing metadata, not signal.
        w = np.asarray(REC709_WEIGHTS, dtype=np.float64)
        lum = arr[..., :3] @ w
    else:
        raise ValueError(f"expected 2D or 3D array, got shape {arr.shape}")

    return np.clip(lum, 0.0, 1.0)


def load_luminance(path: str | Path) -> np.ndarray:
    """Load an image file as float64 luminance in [0, 1]."""
    from PIL import Image

    with Image.open(path) as im:
        im.load()
        arr = np.asarray(im)
    return to_luminance(arr)


def load_stack(paths: list[str | Path]) -> list[np.ndarray]:
    """Load several frames, requiring identical dimensions.

    Mixed dimensions in a frame stack almost always means the frames came from
    different sources or were cropped independently, which invalidates the
    registration and coverage steps. Fail loudly rather than silently resizing.
    """
    frames = [load_luminance(p) for p in paths]
    if not frames:
        raise ValueError("empty frame stack")
    shape = frames[0].shape
    for i, f in enumerate(frames):
        if f.shape != shape:
            raise ValueError(
                f"frame {i} has shape {f.shape}, expected {shape}; "
                "resample upstream and record it, do not resize implicitly"
            )
    return frames
