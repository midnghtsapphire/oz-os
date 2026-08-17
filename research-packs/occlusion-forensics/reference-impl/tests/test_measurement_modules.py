"""Tests for the measurement operators: clarity, occlusion, weave, registration."""

from __future__ import annotations

import numpy as np
import pytest
from scipy import ndimage

from occlusion_forensics.clarity import clarity_map, tile_metric
from occlusion_forensics.deblur import estimate_noise_sigma, gaussian_psf, wiener_deblur
from occlusion_forensics.image_io import to_luminance
from occlusion_forensics.occlusion import structure_tensor
from occlusion_forensics.registration import apply_shift, phase_correlate, register_stack
from occlusion_forensics.weave import analyse_weave


def _sharp(h=64, w=64) -> np.ndarray:
    y, x = np.mgrid[0:h, 0:w]
    return (0.5 + 0.4 * np.sin(x / 2.0) * np.cos(y / 2.0)).clip(0, 1)


def test_clarity_ranks_sharp_above_blurred():
    """Every focus operator must prefer the sharp half of a split image."""
    img = _sharp(64, 64)
    blurred = ndimage.gaussian_filter(img, 3.0)
    split = np.hstack([img[:, :32], blurred[:, 32:]])

    for metric in ("laplacian_variance", "tenengrad", "brenner"):
        scores = tile_metric(split, tile=16, metric=metric)
        left = scores[:, :2].mean()
        right = scores[:, 2:].mean()
        assert left > right, f"{metric} failed to rank sharp above blurred"


def test_clarity_map_anchors_the_sharp_side():
    img = _sharp(64, 64)
    split = np.hstack([img[:, :32], ndimage.gaussian_filter(img, 4.0)[:, 32:]])
    cm = clarity_map(split, tile=16, anchor_quantile=0.5)

    assert cm.grid_shape == (4, 4)
    assert cm.anchors[:, :2].sum() > cm.anchors[:, 2:].sum()
    assert 0.0 <= cm.anchor_fraction <= 1.0
    assert cm.tile_bounds(1, 2) == (16, 32, 32, 48)


def test_clarity_rejects_bad_parameters():
    img = _sharp(32, 32)
    with pytest.raises(ValueError, match="tile must be at least"):
        tile_metric(img, tile=2, metric="tenengrad")
    with pytest.raises(ValueError, match="exceeds image dimensions"):
        tile_metric(img, tile=64, metric="tenengrad")
    with pytest.raises(ValueError, match="anchor_quantile"):
        clarity_map(img, anchor_quantile=1.0)


def test_structure_tensor_separates_oriented_from_isotropic():
    """A grating is coherent; white noise is not."""
    y, x = np.mgrid[0:64, 0:64]
    grating = 0.5 + 0.4 * np.sin(x / 2.0)
    # Deterministic pseudo-noise: no RNG anywhere in this package or its tests.
    noise = 0.5 + 0.4 * np.sin(x * 12.9898 + y * 78.233) * np.cos(x * 39.42 - y * 11.7)

    st_g = structure_tensor(grating, sigma=3.0)
    st_n = structure_tensor(noise, sigma=3.0)

    inner = (slice(8, -8), slice(8, -8))  # avoid boundary effects
    assert st_g.coherence[inner].mean() > 0.9
    assert st_g.coherence[inner].mean() > st_n.coherence[inner].mean()


def test_weave_recovers_known_pitch_and_orientation():
    """A synthetic grating of known period must be measured back correctly."""
    period = 8.0
    y, x = np.mgrid[0:64, 0:64]
    grating = 0.5 + 0.3 * np.sin(2.0 * np.pi * x / period)

    w = analyse_weave(grating)

    assert w.detected
    assert w.pitch_px == pytest.approx(period, rel=0.15)
    # A vertical-bar grating has a horizontal wave vector: 0 or pi.
    assert min(w.orientation_rad, np.pi - w.orientation_rad) < 0.2


def test_weave_reports_undetected_on_aperiodic_input():
    """Smooth, aperiodic content must not be reported as a weave.

    Note for anyone extending this: ``arr[::2, ::2] = c`` is *not* aperiodic —
    it is a period-2 checkerboard, and the analyser correctly reports a
    sqrt(2)-pixel diagonal pitch for it at enormous regularity. Use genuinely
    non-repeating content to test the negative case.
    """
    y, x = np.mgrid[0:32, 0:32]
    ramp = 0.5 + 0.2 * (x / 32.0) - 0.1 * (y / 32.0) ** 2
    w = analyse_weave(ramp)
    assert not w.detected


def test_weave_requires_minimum_size():
    with pytest.raises(ValueError, match="at least 8x8"):
        analyse_weave(np.zeros((4, 4)))


def _blobs(h=64, w=64) -> np.ndarray:
    """Aperiodic scene: registration against a periodic scene is ambiguous.

    ``_sharp`` is a product of sinusoids with a ~12.6 px period, so a shift of
    one period is genuinely indistinguishable from none. That is a property of
    the scene, not a defect in the estimator, and it makes ``_sharp`` unusable
    as a registration fixture.
    """
    y, x = np.mgrid[0:h, 0:w]
    img = np.zeros((h, w))
    for cy, cx, s, a in [(20, 18, 4.0, 0.6), (38, 44, 6.0, 0.5), (46, 20, 3.0, 0.4)]:
        img += a * np.exp(-((y - cy) ** 2 + (x - cx) ** 2) / (2 * s * s))
    return np.clip(img, 0.0, 1.0)


def test_phase_correlation_recovers_known_shift():
    img = _blobs()
    for dy, dx in [(0, 0), (3, -5), (-7, 2), (11, 9)]:
        moved = np.roll(np.roll(img, dy, axis=0), dx, axis=1)
        s = phase_correlate(img, moved)
        assert s.dy == pytest.approx(dy, abs=0.3), f"dy wrong for {(dy, dx)}"
        assert s.dx == pytest.approx(dx, abs=0.3), f"dx wrong for {(dy, dx)}"


def test_shift_round_trip_is_the_sign_convention():
    """apply_shift(moving, phase_correlate(ref, moving)) must reproduce ref."""
    img = _blobs()
    moved = np.roll(np.roll(img, 4, axis=0), -6, axis=1)
    s = phase_correlate(img, moved)
    restored = apply_shift(moved, s, cval=0.0)

    inner = (slice(12, -12), slice(12, -12))  # ignore wraparound at the borders
    assert np.allclose(restored[inner], img[inner], atol=0.02)


def test_hann_window_biases_toward_zero_lag():
    """Documents why `window` defaults to False rather than True."""
    img = _blobs()
    moved = np.roll(np.roll(img, 3, axis=0), -5, axis=1)

    unwindowed = phase_correlate(img, moved, window=False)
    windowed = phase_correlate(img, moved, window=True)

    assert unwindowed.dy == pytest.approx(3, abs=0.3)
    # The taper's common envelope wins at zero lag and destroys the estimate.
    assert abs(windowed.dy) < 1.0


def test_register_stack_reference_is_identity():
    img = _blobs(64, 64)
    shifts = register_stack([img, np.roll(img, 2, axis=0)], reference_index=0)
    assert shifts[0].as_tuple() == (0.0, 0.0)
    assert shifts[1].dy == pytest.approx(2.0, abs=0.3)


def test_register_stack_validates_reference_index():
    with pytest.raises(IndexError):
        register_stack([_sharp(16, 16)], reference_index=3)


def test_deblur_reports_a_finite_cutoff():
    """A deblur without a stated recovery limit is not a measurement."""
    img = _sharp(64, 64)
    psf = gaussian_psf(img.shape, sigma=1.5)
    blurred = np.real(
        np.fft.ifft2(np.fft.fft2(img) * np.fft.fft2(np.fft.ifftshift(psf)))
    )

    result = wiener_deblur(blurred, psf)

    assert 0.0 < result.cutoff_cycles_px <= np.sqrt(0.5)
    assert result.noise_sigma >= 0.0
    # Deconvolution should move the result toward the original.
    assert np.mean((result.image - img) ** 2) < np.mean((blurred - img) ** 2)


def test_deblur_rejects_shape_mismatch():
    with pytest.raises(ValueError, match="pad the psf"):
        wiener_deblur(_sharp(32, 32), gaussian_psf((16, 16), 1.0))


def test_noise_estimate_grows_with_noise():
    img = _sharp(64, 64)
    y, x = np.mgrid[0:64, 0:64]
    speckle = 0.05 * np.sin(x * 12.9898 + y * 78.233)
    assert estimate_noise_sigma(img + speckle) > estimate_noise_sigma(img)


def test_luminance_conversion():
    rgb = np.zeros((4, 4, 3), dtype=np.uint8)
    rgb[..., 1] = 255  # pure green
    lum = to_luminance(rgb)
    assert lum.dtype == np.float64
    assert np.allclose(lum, 0.7152)
    assert to_luminance(np.zeros((4, 4))).shape == (4, 4)
    with pytest.raises(ValueError, match="2D or 3D"):
        to_luminance(np.zeros((2, 2, 2, 2)))
