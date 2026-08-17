"""Structured findings with mandatory provenance.

Every claim carries the pixel region it came from, the operator that produced
it, and an uncertainty. A claim that cannot supply all three cannot be
constructed — the dataclass rejects it. This is deliberate: the usual failure
mode of forensic image analysis is not bad arithmetic, it is a confident
sentence with no measurement behind it.

``NOT_MEASURABLE`` attributes are enumerated here rather than left to the
caller's judgement. Each entry records the physical reason no pixel operation
can yield it, so the refusal is a citable technical result rather than a policy
the next integrator can toggle off.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

__all__ = [
    "Determination",
    "NOT_MEASURABLE",
    "Region",
    "Claim",
    "Report",
    "check_measurable",
]


class Determination(str, Enum):
    """What the pixels support. There is no verdict for "asked confidently"."""

    MEASURED = "MEASURED"  # a number, with an uncertainty, from named pixels
    BOUNDED = "BOUNDED"  # only an interval or inequality is supported
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"  # measurable in principle, not here
    NOT_MEASURABLE = "NOT_MEASURABLE"  # no pixel operation yields this, ever


# Attributes for which no imaging measurement exists, with the reason.
# These are not "hard" — they are outside the range of the instrument, in the
# same sense that a thermometer does not report mass.
NOT_MEASURABLE: dict[str, str] = {
    "race": (
        "No pixel quantity maps to this. Observed skin luminance is the product "
        "of illuminant spectrum, sensor spectral response and white balance. "
        "Under IR or night-vision sensors the response is dominated by IR "
        "reflectance, which is near-uninformative about melanin. Any contrast "
        "normalisation applied during preprocessing destroys absolute tone "
        "outright. The quantity is not degraded here; it was never measured."
    ),
    "ethnicity": (
        "A social and self-ascribed category, not a physical property of a "
        "surface. It has no radiometric definition, so no imaging operator can "
        "estimate it, at any resolution."
    ),
    "nationality": (
        "A legal status held in state records. It has no optical correlate."
    ),
    "name": (
        "An identifier held in external records. Nothing in a photograph "
        "determines it; a claimed match is a database lookup, and its error "
        "rate belongs to the database, not to this instrument."
    ),
    "identity": (
        "Identification is a comparison against an enrolled reference under a "
        "stated false-match rate. It is not an image-processing output, and it "
        "cannot be performed against a reconstruction — a reconstruction shares "
        "its detail with the prior that generated it, not with any person."
    ),
    "occupation": (
        "Not a property of a face. Clothing and context may support an "
        "inference about a role, but that inference belongs to an investigator "
        "with case knowledge, not to a pixel operator."
    ),
    "accent": (
        "An acoustic property. It is absent from image data by definition."
    ),
    "sex": (
        "Reported facial morphometrics are population-overlapping distributions, "
        "not a per-individual determination, and under occlusion the landmarks "
        "required to compute them are themselves unmeasured. Any output would "
        "be a prior evaluated on missing data."
    ),
    "gender": (
        "Self-ascribed. No physical measurement addresses it."
    ),
    "occluded_facial_geometry": (
        "The masking operator has a non-trivial null space; the data constrains "
        "nothing about it. Compressed-sensing recovery would require the "
        "measurement operator to satisfy a restricted isometry property, which "
        "a contiguous physical occluder violates by construction. Use "
        "coverage.coverage_report to test whether multi-frame observation "
        "covers the region instead."
    ),
}


def check_measurable(attribute: str) -> None:
    """Raise if ``attribute`` is outside the instrument's range.

    Call this at the top of any function tempted to report a person-attribute.
    """
    key = attribute.strip().lower().replace(" ", "_")
    if key in NOT_MEASURABLE:
        raise ValueError(
            f"{attribute!r} is NOT_MEASURABLE from image data: {NOT_MEASURABLE[key]}"
        )


@dataclass(frozen=True)
class Region:
    """A pixel rectangle in reference-frame coordinates, half-open."""

    row0: int
    row1: int
    col0: int
    col1: int

    def __post_init__(self) -> None:
        if self.row1 <= self.row0 or self.col1 <= self.col0:
            raise ValueError(f"empty or inverted region: {self}")

    @property
    def area_px(self) -> int:
        return (self.row1 - self.row0) * (self.col1 - self.col0)

    def as_dict(self) -> dict[str, int]:
        return {
            "row0": self.row0,
            "row1": self.row1,
            "col0": self.col0,
            "col1": self.col1,
        }


@dataclass(frozen=True)
class Claim:
    """A single finding. Cannot be constructed without provenance."""

    attribute: str
    determination: Determination
    method: str
    region: Region | None = None
    value: float | str | None = None
    uncertainty: float | None = None
    units: str | None = None
    note: str = ""

    def __post_init__(self) -> None:
        # Out-of-range attributes may only ever appear as an explicit
        # NOT_MEASURABLE record. Any attempt to attach a value to one is a
        # construction error, caught here rather than in review.
        if self.determination is not Determination.NOT_MEASURABLE:
            check_measurable(self.attribute)
        elif self.value is not None:
            raise ValueError(
                f"NOT_MEASURABLE claim {self.attribute!r} must not carry a value"
            )

        if self.determination is Determination.MEASURED:
            if self.region is None:
                raise ValueError(
                    f"MEASURED claim {self.attribute!r} needs a region: a measurement "
                    "with no stated extent cannot be re-checked"
                )
            if self.value is None:
                raise ValueError(f"MEASURED claim {self.attribute!r} needs a value")
            if self.uncertainty is None:
                raise ValueError(
                    f"MEASURED claim {self.attribute!r} needs an uncertainty; a point "
                    "estimate without one is not a measurement"
                )
        if not self.method:
            raise ValueError(f"claim {self.attribute!r} needs a named method")

    def as_dict(self) -> dict[str, Any]:
        return {
            "attribute": self.attribute,
            "determination": self.determination.value,
            "method": self.method,
            "region": self.region.as_dict() if self.region else None,
            "value": self.value,
            "uncertainty": self.uncertainty,
            "units": self.units,
            "note": self.note,
        }


@dataclass
class Report:
    """A complete analysis result."""

    manifest: dict[str, Any]
    claims: list[Claim] = field(default_factory=list)
    coverage: dict[str, Any] | None = None
    processing_log: list[str] = field(default_factory=list)

    def add(self, claim: Claim) -> None:
        self.claims.append(claim)

    def log(self, message: str) -> None:
        self.processing_log.append(message)

    def declare_not_measurable(self, attribute: str) -> None:
        """Record an explicit refusal for an attribute someone asked about.

        Recording the question and the reason is better than silence: it shows
        the attribute was considered and why it was excluded, which is exactly
        what an opposing analyst will ask.
        """
        key = attribute.strip().lower().replace(" ", "_")
        reason = NOT_MEASURABLE.get(key, "no imaging operator yields this attribute")
        self.claims.append(
            Claim(
                attribute=attribute,
                determination=Determination.NOT_MEASURABLE,
                method="range-of-instrument check",
                note=reason,
            )
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "manifest": self.manifest,
            "coverage": self.coverage,
            "claims": [c.as_dict() for c in self.claims],
            "processing_log": list(self.processing_log),
        }

    def to_json(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True, indent=2, default=str)
