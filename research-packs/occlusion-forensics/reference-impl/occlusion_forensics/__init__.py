"""Deterministic occlusion forensics.

A measurement instrument for occluded imagery. It reports what the pixels
support and marks everything else as unmeasured, including — permanently — the
geometry behind an occluder.

Scope, stated once so it is not mistaken for an oversight:

  * There is no face reconstruction here, and no inpainting of any kind.
  * There is no attribute inference: no race, ethnicity, sex, gender, name,
    nationality, occupation or identity estimator. ``report.NOT_MEASURABLE``
    records the physical reason for each.
  * There is no biometric matching and no face detection.

What it does instead: locate the regions that actually carry detail, segment the
occluder, characterise it as a material, and — where multiple frames observed
the same scene through a *moving* occluder — recover the parts that were
genuinely seen, leaving the rest as NaN.

See ``coverage`` for the argument that makes the difference between those two
operations a mathematical one rather than a matter of taste.
"""

from __future__ import annotations

__version__ = "0.1.0"

from . import (  # noqa: F401
    clarity,
    coverage,
    deblur,
    determinism,
    image_io,
    occlusion,
    recovery,
    registration,
    report,
    weave,
)
from .clarity import ClarityMap, clarity_map
from .coverage import CoverageReport, coverage_report
from .deblur import DeblurResult, wiener_deblur
from .determinism import RunManifest
from .occlusion import OcclusionMask, occlusion_mask
from .pipeline import analyse_stack
from .recovery import Recovery, fuse_visible, iterative_back_projection
from .registration import Shift, register_stack
from .report import NOT_MEASURABLE, Claim, Determination, Region, Report
from .weave import WeaveDescriptor, analyse_weave

__all__ = [
    "__version__",
    "ClarityMap",
    "clarity_map",
    "CoverageReport",
    "coverage_report",
    "DeblurResult",
    "wiener_deblur",
    "RunManifest",
    "OcclusionMask",
    "occlusion_mask",
    "analyse_stack",
    "Recovery",
    "fuse_visible",
    "iterative_back_projection",
    "Shift",
    "register_stack",
    "NOT_MEASURABLE",
    "Claim",
    "Determination",
    "Region",
    "Report",
    "WeaveDescriptor",
    "analyse_weave",
]
