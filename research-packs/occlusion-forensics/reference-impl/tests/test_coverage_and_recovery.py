"""The tests that matter: the null space must survive every code path.

If any of these fail, the package has become a generator and must not ship.
"""

from __future__ import annotations

import numpy as np
import pytest

from occlusion_forensics.coverage import coverage_report
from occlusion_forensics.recovery import fuse_visible, iterative_back_projection
from occlusion_forensics.registration import Shift


def _scene(h: int = 64, w: int = 64) -> np.ndarray:
    """A deterministic textured test scene."""
    y, x = np.mgrid[0:h, 0:w]
    return (
        0.5
        + 0.2 * np.sin(x / 3.0)
        + 0.15 * np.cos(y / 5.0)
        + 0.1 * np.sin((x + y) / 7.0)
    ).clip(0.0, 1.0)


def test_static_occluder_leaves_null_space():
    """An occluder that never moves annihilates a subspace no fusion can restore."""
    scene = _scene()
    visible = np.ones_like(scene, dtype=bool)
    visible[20:40, 20:40] = False  # same hole in every frame

    frames = [scene, scene, scene, scene]
    masks = [visible, visible, visible, visible]
    shifts = [Shift(0.0, 0.0, 1.0)] * 4

    cov = coverage_report(masks, shifts)

    assert cov.null_space.sum() == 20 * 20
    assert cov.null_space_fraction == pytest.approx(400 / scene.size)
    assert not cov.summary()["fully_covered"]

    rec = fuse_visible(frames, masks, shifts, cov)
    # The hole must be NaN, not a plausible value.
    assert np.all(np.isnan(rec.image[20:40, 20:40]))
    assert not rec.support[20:40, 20:40].any()
    # And everything outside it must be recovered exactly.
    outside = ~cov.null_space
    assert np.allclose(rec.image[outside], scene[outside], atol=1e-9)


def test_moving_occluder_closes_the_null_space():
    """When the occluder moves, the union of observations can cover everything."""
    scene = _scene()

    m1 = np.ones_like(scene, dtype=bool)
    m1[20:40, 20:40] = False
    m2 = np.ones_like(scene, dtype=bool)
    m2[20:40, 40:60] = False  # hole elsewhere

    cov = coverage_report([m1, m2], [Shift(0.0, 0.0, 1.0)] * 2)

    assert cov.null_space.sum() == 0
    assert cov.summary()["fully_covered"]
    assert cov.mean_multiplicity > 1.0

    rec = fuse_visible([scene, scene], [m1, m2], [Shift(0.0, 0.0, 1.0)] * 2, cov)
    assert rec.support.all()
    assert not np.isnan(rec.image).any()
    assert np.allclose(rec.image, scene, atol=1e-9)


def test_ibp_cannot_create_support():
    """Back-projection refines the estimate; it must never widen it."""
    scene = _scene()
    visible = np.ones_like(scene, dtype=bool)
    visible[10:30, 10:30] = False

    frames = [scene, scene]
    masks = [visible, visible]
    shifts = [Shift(0.0, 0.0, 1.0)] * 2

    cov = coverage_report(masks, shifts)
    rec = fuse_visible(frames, masks, shifts, cov)
    refined = iterative_back_projection(rec, frames, masks, shifts, iterations=25)

    assert np.array_equal(refined.support, rec.support)
    assert np.all(np.isnan(refined.image[10:30, 10:30]))
    assert refined.unrecovered_fraction == rec.unrecovered_fraction


def test_coverage_rejects_mismatched_stack():
    masks = [np.ones((8, 8), dtype=bool)]
    with pytest.raises(ValueError, match="every frame needs a registration"):
        coverage_report(masks, [])


def test_fuse_requires_matching_coverage():
    scene = _scene(32, 32)
    masks = [np.ones_like(scene, dtype=bool)]
    shifts = [Shift(0.0, 0.0, 1.0)]
    other = coverage_report([np.ones((16, 16), dtype=bool)], shifts)
    with pytest.raises(ValueError, match="same stack"):
        fuse_visible([scene], masks, shifts, other)


def test_dispersion_flags_disagreeing_frames():
    """Contradictory observations must be flagged, not silently averaged."""
    a = np.full((32, 32), 0.2)
    b = np.full((32, 32), 0.8)
    masks = [np.ones((32, 32), dtype=bool)] * 2
    shifts = [Shift(0.0, 0.0, 1.0)] * 2

    cov = coverage_report(masks, shifts)
    rec = fuse_visible([a, b], masks, shifts, cov)

    assert np.allclose(rec.image, 0.5)
    assert np.allclose(rec.dispersion, 0.3)
    assert rec.disagreement_flags(threshold=0.1).all()
