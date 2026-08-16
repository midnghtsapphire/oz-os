# NON_GOALS — What This Pack Will Not Build

Stated explicitly so the absences read as decisions rather than gaps, and so a
future agent extending the pack does not "helpfully" add them.

## Not built, and not to be added

| Capability | Reason |
|---|---|
| Face reconstruction / de-occlusion inpainting | The masking operator's null space is unconstrained by the data. Output would be a sample from a training prior, not an estimate of the subject. See `methods/04-rejected-and-provenance.md`. |
| Face frontalisation | Compounds the above by also synthesising the occluded hemisphere. |
| Race / ethnicity estimation | No pixel quantity maps to it. Observed skin luminance is the product of illuminant spectrum, sensor response and white balance; under IR it is dominated by IR reflectance. Contrast normalisation destroys absolute tone outright. Not degraded — never measured. |
| Sex / gender estimation | Reported facial morphometrics are population-overlapping distributions, not per-individual determinations, and under occlusion the required landmarks are themselves unmeasured. |
| Nationality, name, occupation, accent | Legal status, database identifiers, social role and acoustics respectively. None has an optical correlate. |
| Biometric matching / identification | Identification is a comparison against an enrolled reference under a stated false-match rate. It is not an image-processing output, and it cannot be performed against a reconstruction. |
| Face detection or landmarking | Not needed by any method here, and its presence would invite the above. |

These are enforced in code, not just documented. `report.NOT_MEASURABLE`
enumerates each with its physical reason, and `report.Claim` raises on any
attempt to attach a value to one. `tests/test_report_and_determinism.py`
parametrises over the whole registry to keep that true.

## The verdict-hardcoding anti-pattern

This pack was commissioned from a prompt that specified fixed output labels:
`Eye color → DETERMINATE`, `Race/ethnicity → DETERMINATE`,
`Biological sex → DETERMINATE`.

Fixing a verdict independent of the evidence guarantees a positive assertion
whether or not the pixels support one. That is not an instrument; it is a
generator with a constant output, and it would fail a *Daubert* challenge on the
first question about error rate.

The design rule that follows: **determination labels are outputs, never inputs.**
`Determination` has four values — `MEASURED`, `BOUNDED`, `INSUFFICIENT_DATA`,
`NOT_MEASURABLE` — and which one appears is decided by the measurement, with
`MEASURED` requiring a region, a value and an uncertainty before it can be
constructed at all.

## What replaced the rejected capability

Not nothing. The pack ships the measurement half in full — clarity anchoring,
occluder segmentation, weave characterisation, registration, the coverage gate,
gated multi-frame fusion, bounded deblur, and synthetic-detail detection. On the
case documented in `methods/04-rejected-and-provenance.md`, that toolset produced
the actually decisive finding: the supplied "enhanced" frames were one source
frame re-rendered, the chain had destroyed 70 % of the original edge energy, and
the final frame contained drawn structure absent from the source.

That is what the honest tool had to say, and it mattered more than a
reconstruction would have.
