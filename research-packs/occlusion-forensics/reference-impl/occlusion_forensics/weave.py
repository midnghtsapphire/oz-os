"""Fabric weave characterisation by Fourier analysis.

A periodic weave produces a pair of conjugate peaks in the 2D power spectrum.
Their radius gives the pitch, their angle gives the thread orientation, and the
peak's prominence over the local spectral background gives the regularity.

These are material measurements. They describe the occluder, which is a real,
fully visible object. They support conclusions like "the same knit appears in
frame 3 and frame 11" — the kind of claim that is actually defensible, because
the evidence is present in the pixels rather than absent from them.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = ["WeaveDescriptor", "power_spectrum", "analyse_weave"]


@dataclass
class WeaveDescriptor:
    """Periodicity descriptor for one image region."""

    pitch_px: float  # spatial period of the dominant structure, in pixels
    orientation_rad: float  # direction of the dominant wave vector, [0, pi)
    regularity: float  # peak power / median background power
    peak_frequency: tuple[float, float]  # (fy, fx) in cycles per pixel
    detected: bool  # False when no peak clears the prominence floor

    def as_dict(self) -> dict[str, object]:
        return {
            "pitch_px": self.pitch_px,
            "orientation_rad": self.orientation_rad,
            "orientation_deg": float(np.degrees(self.orientation_rad)),
            "regularity": self.regularity,
            "peak_frequency_cyc_px": list(self.peak_frequency),
            "detected": self.detected,
        }


def power_spectrum(region: np.ndarray) -> np.ndarray:
    """Windowed, mean-removed, fftshift-centred power spectrum.

    Mean removal kills the DC spike that would otherwise dominate every search.
    The separable Hann window suppresses the cross-shaped spectral leakage that
    a hard rectangular crop produces, which is otherwise easy to misread as a
    pair of axis-aligned weave peaks.
    """
    r = np.asarray(region, dtype=np.float64)
    if r.ndim != 2:
        raise ValueError("region must be 2D")
    if min(r.shape) < 8:
        raise ValueError("region must be at least 8x8 to resolve a weave")

    r = r - r.mean()
    wy = np.hanning(r.shape[0])
    wx = np.hanning(r.shape[1])
    r = r * np.outer(wy, wx)

    spec = np.fft.fftshift(np.fft.fft2(r))
    return np.abs(spec) ** 2


def analyse_weave(
    region: np.ndarray,
    min_regularity: float = 4.0,
    min_periods: float = 4.0,
) -> WeaveDescriptor:
    """Find the dominant periodic component of a region.

    ``min_regularity`` is the ratio by which the peak must exceed the median
    spectral background before a weave is declared detected. Below it, the
    descriptor is returned with ``detected=False`` and the numbers should not be
    quoted — a spectrum with no real peak still has a maximum somewhere, and
    reporting that maximum as a "pitch" is how noise becomes a finding.
    """
    ps = power_spectrum(region)
    h, w = ps.shape
    cy, cx = h // 2, w // 2

    # Restrict the search to pitches this region can actually evidence.
    #
    # Lower bound on frequency: periodicity is not established by a single
    # repeat. Requiring `min_periods` cycles inside the window is the whole
    # difference between "measured a weave" and "fitted a sinusoid to an
    # illumination gradient" — a smooth ramp will always place its maximum at
    # the lowest searchable frequency, and without this bound that maximum gets
    # reported as a weave pitch with high apparent prominence.
    #
    # Upper bound: 0.5 cycles/px is Nyquist. Structure finer than a two-pixel
    # pitch is aliased and its apparent frequency is not its real one.
    yy, xx = np.ogrid[:h, :w]
    radius = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)

    extent = float(min(h, w))
    min_cycles = max(min_periods, 2.0)
    # radius in bins maps to cycles across the window, so the bound is direct.
    searchable = (radius >= min_cycles) & (radius <= 0.5 * extent)

    if not searchable.any():
        return WeaveDescriptor(0.0, 0.0, 0.0, (0.0, 0.0), False)

    masked = np.where(searchable, ps, -np.inf)
    idx = int(np.argmax(masked))
    py, px = divmod(idx, w)
    peak = float(ps[py, px])

    # Background is measured in an annulus at the peak's own radius rather than
    # over the whole spectrum. Natural images are approximately 1/f, so a
    # global median is dominated by the high-frequency tail and makes any
    # low-frequency leakage look enormously significant — a smooth ramp scored
    # 6.8e9 under a global median. The right null model asks whether this peak
    # is anomalous *among components of the same frequency*, which is what a
    # real weave is and what spectral leakage is not.
    peak_radius = np.sqrt((py - cy) ** 2 + (px - cx) ** 2)
    band = searchable & (np.abs(radius - peak_radius) <= 1.5)
    # Exclude the peak's own neighbourhood so it does not inflate its baseline.
    band &= np.sqrt((yy - py) ** 2 + (xx - px) ** 2) > 2.0

    if band.sum() < 8:
        return WeaveDescriptor(0.0, 0.0, 0.0, (0.0, 0.0), False)

    # The peak must be a strict local maximum along its own radial ray.
    #
    # This is what separates a weave from spectral leakage, and prominence
    # tests alone cannot do it. Leakage from an aperiodic gradient decays
    # monotonically with frequency (measured on a linear ramp: 2.3e0, 1.3e-1,
    # 1.9e-2, 4.4e-3 at successive radii), so its maximum inside any search
    # band sits at the band's inner edge and is still rising inward. A real
    # grating produces an isolated peak that falls off on *both* sides
    # (measured: 6.6e-1, 5.8e3, 2.2e4, 5.8e3, 6.7e-1). Requiring a strict
    # radial local maximum accepts the second and rejects the first.
    if peak_radius > 0:
        uy, ux = (py - cy) / peak_radius, (px - cx) / peak_radius
        neighbours = []
        for dr in (-1.5, 1.5):
            ny = int(round(cy + (peak_radius + dr) * uy))
            nx = int(round(cx + (peak_radius + dr) * ux))
            if 0 <= ny < h and 0 <= nx < w:
                neighbours.append(float(ps[ny, nx]))
        if neighbours and not all(peak > n for n in neighbours):
            return WeaveDescriptor(
                pitch_px=0.0,
                orientation_rad=0.0,
                regularity=0.0,
                peak_frequency=(0.0, 0.0),
                detected=False,
            )

    background = float(np.median(ps[band]))
    total = float(ps[searchable].sum())

    # Two conditions, because either alone is foolable: the peak must stand out
    # from its own frequency band, and it must carry a non-trivial share of the
    # spectrum. Leakage satisfies neither; a weave satisfies both.
    prominence = peak / background if background > 0 else 0.0
    share = peak / total if total > 0 else 0.0
    regularity = prominence * min(1.0, share / 0.01)

    # Convert the shifted bin index to signed cycles per pixel.
    fy = (py - cy) / h
    fx = (px - cx) / w
    freq = float(np.hypot(fy, fx))

    pitch = 1.0 / freq if freq > 0 else 0.0
    # The wave vector direction; mod pi because a grating and its 180-degree
    # rotation are the same grating.
    orientation = float(np.mod(np.arctan2(fy, fx), np.pi))

    return WeaveDescriptor(
        pitch_px=pitch,
        orientation_rad=orientation,
        regularity=regularity,
        peak_frequency=(float(fy), float(fx)),
        detected=regularity >= min_regularity,
    )
