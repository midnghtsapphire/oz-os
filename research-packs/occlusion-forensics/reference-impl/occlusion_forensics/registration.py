"""Sub-pixel translational registration by phase correlation.

Registration is the precondition for everything multi-frame. If frames are not
aligned to better than a pixel, fusing them destroys detail instead of adding
it, and the coverage test computes the union of the wrong regions.

Phase correlation is used rather than intensity correlation because it is
invariant to overall brightness and contrast changes between frames — common
when a subject moves between lighting zones, or when auto-exposure adjusts
mid-sequence.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import ndimage

__all__ = ["Shift", "phase_correlate", "register_stack", "apply_shift"]


@dataclass(frozen=True)
class Shift:
    """Translation of a frame relative to the reference, in pixels."""

    dy: float
    dx: float
    peak: float  # normalised correlation peak height, [0, 1]

    def as_tuple(self) -> tuple[float, float]:
        return (self.dy, self.dx)


def _parabolic_offset(a: float, b: float, c: float) -> float:
    """Sub-sample peak offset from three samples straddling a maximum.

    Fits y = ax^2 + bx + c through (-1, a), (0, b), (1, c) and returns the
    vertex. Returns 0 for a degenerate (flat) triple rather than dividing by
    zero.
    """
    denom = a - 2.0 * b + c
    if denom == 0.0:
        return 0.0
    offset = 0.5 * (a - c) / denom
    # A parabolic fit is only meaningful within the sample it was fit to.
    return float(np.clip(offset, -1.0, 1.0))


def phase_correlate(
    reference: np.ndarray, moving: np.ndarray, window: bool = False
) -> Shift:
    """Estimate the translation that aligns ``moving`` with ``reference``.

    Sign convention: the returned shift is what must be *removed* from
    ``moving``, so ``apply_shift(moving, phase_correlate(ref, moving))``
    reproduces ``ref``. That round trip is the definition and is what the tests
    assert; reasoning about the raw correlation index instead is how sign errors
    survive review.

    ``window`` applies a separable Hann taper before the transform. It defaults
    to *off*, which is not an oversight. Phase correlation whitens the cross
    spectrum, and an identical spatial taper on both inputs survives whitening
    as a common envelope that correlates perfectly at zero lag — a spurious peak
    that beats the true one for small displacements. Measured on synthetic
    aperiodic input, a Hann taper turned a clean 1.000 peak at the true shift
    into a 0.508 artefact at (0, 0). Enable it only when edge discontinuity
    genuinely dominates, and check ``peak`` when you do.

    Note also that phase correlation on a *periodic* scene is ambiguous by
    nature: a shift of one period is indistinguishable from none. A low ``peak``
    on textured, repetitive content usually means that, not a small shift.
    """
    if reference.shape != moving.shape:
        raise ValueError(
            f"shape mismatch: {reference.shape} vs {moving.shape}; "
            "register only same-size frames"
        )

    h, w = reference.shape
    a = reference - reference.mean()
    b = moving - moving.mean()
    if window:
        taper = np.outer(np.hanning(h), np.hanning(w))
        a = a * taper
        b = b * taper

    fa = np.fft.fft2(a)
    fb = np.fft.fft2(b)

    cross = fa * np.conj(fb)
    magnitude = np.abs(cross)
    # Whitening is the whole point of *phase* correlation; the epsilon only
    # guards frequencies where both frames have literally zero energy.
    cross = cross / np.where(magnitude == 0, 1.0, magnitude)

    corr = np.real(np.fft.ifft2(cross))

    idx = int(np.argmax(corr))
    py, px = divmod(idx, w)
    peak = float(corr[py, px])

    # Refine to sub-pixel using neighbours, with wraparound: the correlation
    # surface is periodic, so index 0's left neighbour is index -1.
    dy = _parabolic_offset(
        float(corr[(py - 1) % h, px]), peak, float(corr[(py + 1) % h, px])
    )
    dx = _parabolic_offset(
        float(corr[py, (px - 1) % w]), peak, float(corr[py, (px + 1) % w])
    )

    # Map the peak from [0, N) to the signed range [-N/2, N/2).
    sy = py - h if py > h // 2 else py
    sx = px - w if px > w // 2 else px

    # Negate: the correlation peak sits at the displacement of `reference`
    # relative to `moving`, and callers need the opposite — the correction to
    # apply to `moving`. See the round-trip convention in the docstring.
    return Shift(dy=-(float(sy) + dy), dx=-(float(sx) + dx), peak=peak)


def apply_shift(image: np.ndarray, shift: Shift, order: int = 3, cval: float = np.nan) -> np.ndarray:
    """Resample ``image`` by ``-shift``, bringing it into reference coordinates.

    Out-of-bounds pixels default to NaN rather than 0. A zero would be
    indistinguishable from a genuinely black pixel and would silently pull
    fused averages toward black; NaN propagates as "no data", which is what it
    is.
    """
    return ndimage.shift(
        image,
        shift=(-shift.dy, -shift.dx),
        order=order,
        mode="constant",
        cval=cval,
        prefilter=True,
    )


def register_stack(frames: list[np.ndarray], reference_index: int = 0) -> list[Shift]:
    """Register every frame against one reference frame.

    A single reference (rather than pairwise chaining) avoids accumulating drift
    across a long sequence. It does assume the reference overlaps every other
    frame; check the returned ``peak`` values, and treat a low peak as a failed
    registration rather than a small shift.
    """
    if not frames:
        raise ValueError("empty frame stack")
    if not 0 <= reference_index < len(frames):
        raise IndexError(f"reference_index {reference_index} out of range")

    ref = frames[reference_index]
    shifts: list[Shift] = []
    for i, f in enumerate(frames):
        if i == reference_index:
            shifts.append(Shift(0.0, 0.0, 1.0))
        else:
            shifts.append(phase_correlate(ref, f))
    return shifts
