"""Tests for the reporting contract and run reproducibility."""

from __future__ import annotations

import json

import numpy as np
import pytest

from occlusion_forensics.determinism import RunManifest, canonical_json, sha256_array
from occlusion_forensics.pipeline import analyse_stack
from occlusion_forensics.report import (
    NOT_MEASURABLE,
    Claim,
    Determination,
    Region,
    Report,
    check_measurable,
)


def _scene(h=64, w=64) -> np.ndarray:
    y, x = np.mgrid[0:h, 0:w]
    return (0.5 + 0.2 * np.sin(x / 3.0) + 0.15 * np.cos(y / 5.0)).clip(0, 1)


@pytest.mark.parametrize("attribute", sorted(NOT_MEASURABLE))
def test_out_of_range_attributes_cannot_become_claims(attribute):
    """The refusal is structural: these attributes cannot carry a value."""
    with pytest.raises(ValueError, match="NOT_MEASURABLE"):
        check_measurable(attribute)

    with pytest.raises(ValueError, match="NOT_MEASURABLE"):
        Claim(
            attribute=attribute,
            determination=Determination.MEASURED,
            method="whatever",
            region=Region(0, 4, 0, 4),
            value=1.0,
            uncertainty=0.1,
        )


def test_attribute_matching_is_case_and_space_insensitive():
    with pytest.raises(ValueError):
        check_measurable("  Race  ")
    with pytest.raises(ValueError):
        check_measurable("Occluded Facial Geometry")


def test_not_measurable_claim_may_be_recorded_without_a_value():
    rpt = Report(manifest={})
    rpt.declare_not_measurable("identity")
    (claim,) = rpt.claims
    assert claim.determination is Determination.NOT_MEASURABLE
    assert claim.value is None
    assert "enrolled reference" in claim.note


def test_not_measurable_claim_rejects_a_value():
    with pytest.raises(ValueError, match="must not carry a value"):
        Claim(
            attribute="race",
            determination=Determination.NOT_MEASURABLE,
            method="x",
            value="anything",
        )


def test_measured_claims_require_full_provenance():
    for kwargs in (
        {"region": None, "value": 1.0, "uncertainty": 0.1},
        {"region": Region(0, 2, 0, 2), "value": None, "uncertainty": 0.1},
        {"region": Region(0, 2, 0, 2), "value": 1.0, "uncertainty": None},
    ):
        with pytest.raises(ValueError):
            Claim(
                attribute="occluder_weave_pitch",
                determination=Determination.MEASURED,
                method="fft",
                **kwargs,
            )


def test_region_rejects_empty_extent():
    with pytest.raises(ValueError, match="empty or inverted"):
        Region(5, 5, 0, 3)
    with pytest.raises(ValueError, match="empty or inverted"):
        Region(0, 3, 7, 2)


def test_manifest_hash_is_stable_and_parameter_sensitive():
    a = RunManifest(tool_version="0.1.0")
    a.parameters = {"tile": 16, "sigma": 2.0}
    b = RunManifest(tool_version="0.1.0")
    b.parameters = {"sigma": 2.0, "tile": 16}  # same content, different order
    assert a.manifest_hash() == b.manifest_hash()

    c = RunManifest(tool_version="0.1.0")
    c.parameters = {"tile": 32, "sigma": 2.0}
    assert c.manifest_hash() != a.manifest_hash()


def test_manifest_hash_excludes_outputs():
    """Same experiment, different results, must be detectable as such."""
    m = RunManifest(tool_version="0.1.0")
    m.parameters = {"tile": 16}
    before = m.manifest_hash()
    m.add_output("recovered", np.ones((4, 4)))
    assert m.manifest_hash() == before
    assert "recovered" in json.loads(m.to_json())["outputs"]


def test_canonical_json_sorts_keys():
    assert canonical_json({"b": 1, "a": 2}) == '{"a":2,"b":1}'


def test_array_hash_ignores_stride_layout():
    a = np.arange(24, dtype=np.float64).reshape(4, 6)
    assert sha256_array(a[:, ::2]) == sha256_array(np.ascontiguousarray(a[:, ::2]))
    assert sha256_array(a) != sha256_array(a.T)


def test_pipeline_is_reproducible_and_declares_refusals():
    scene = _scene()
    occluded = scene.copy()
    y, x = np.mgrid[0:64, 0:64]
    weave = 0.3 + 0.2 * np.sin(2 * np.pi * x / 4.0)
    occluded[16:48, 16:48] = weave[16:48, 16:48]

    first = analyse_stack([occluded], tile=16)
    second = analyse_stack([occluded], tile=16)

    assert first.report.manifest["manifest_hash"] == second.report.manifest["manifest_hash"]
    assert first.report.to_json() == second.report.to_json()

    refused = {
        c.attribute for c in first.report.claims
        if c.determination is Determination.NOT_MEASURABLE
    }
    assert {"identity", "race", "sex", "occluded_facial_geometry"} <= refused

    assert first.report.coverage is not None
    assert first.report.coverage["n_frames"] == 1


def test_single_frame_stack_yields_unrecovered_region():
    """The common real case: one frame, one occluder, a permanent hole."""
    scene = _scene()
    occluded = scene.copy()
    y, x = np.mgrid[0:64, 0:64]
    occluded[16:48, 16:48] = (0.3 + 0.2 * np.sin(2 * np.pi * x / 4.0))[16:48, 16:48]

    result = analyse_stack([occluded], tile=16, ibp_iterations=0)

    assert result.coverage.null_space.any(), "an occluder should produce a null space"
    assert result.recovery is not None
    assert np.isnan(result.recovery.image).any()

    insufficient = [
        c for c in result.report.claims
        if c.determination is Determination.INSUFFICIENT_DATA
    ]
    assert insufficient, "the null space must be reported, not omitted"
    assert "no constraint" in insufficient[0].note
