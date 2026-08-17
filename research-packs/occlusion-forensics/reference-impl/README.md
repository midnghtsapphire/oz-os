# occlusion_forensics — reference implementation

Deterministic measurement instrument for occluded imagery. Classical CV only:
no learned priors, no RNG anywhere, bit-reproducible under a hash-logged
parameter set.

## Install and test

```bash
pip install -r requirements.txt
python -m pytest tests/ -q          # 43 tests
```

## Use

```bash
python -m occlusion_forensics analyse frame*.png \
    --json report.json --recovered out.png --support support.png
```

```python
from occlusion_forensics import analyse_stack
from occlusion_forensics.image_io import load_stack

result = analyse_stack(load_stack(["f1.png", "f2.png", "f3.png"]))
print(result.coverage.summary())
print(result.report.to_json())
```

## The one thing to understand

`recovery.image` is `NaN` wherever `coverage.counts == 0`, and no parameter
changes that. Those holes are the product, not a defect: they mark exactly where
the data placed no constraint. The gate is computed from observation geometry
*before* any reconstruction exists, so it cannot be rationalised after seeing an
appealing result.

Recovery becomes available only when the occluder **moves relative to the scene**
across frames, so the union of observations covers what any single frame hid.
Four screenshots of one video frame are one observation, not four —
`register_stack` will report `dy = dx = 0.000` and coverage will not close.

## Modules

| Module | Does |
|---|---|
| `clarity` | Per-tile Laplacian variance / Tenengrad / Brenner; 2-of-3 anchor voting |
| `occlusion` | Structure-tensor coherence → binary visibility mask |
| `weave` | 2D FFT pitch, orientation, regularity, with three false-positive guards |
| `registration` | Sub-pixel phase correlation (`window=False` by default — see docstring) |
| `coverage` | **The gate.** Per-pixel observation counts across registered frames |
| `recovery` | Coverage-gated fusion + iterative back-projection |
| `deblur` | Wiener with measured noise floor and reported cutoff frequency |
| `report` | Claims with mandatory provenance; `NOT_MEASURABLE` registry |
| `determinism` | Run manifest, canonical parameter hashing |
| `pipeline` | The stages in the order the argument requires |

## Not included

No face reconstruction, inpainting, frontalisation, face detection, biometric
matching, or any person-attribute estimator. `report.NOT_MEASURABLE` records the
physical reason for each, and `Claim` raises on any attempt to attach a value to
one. See `../NON_GOALS.md`.

## Determinism contract

Two runs with the same `manifest_hash` must produce byte-identical output.
The manifest hash covers inputs, parameters and library versions but *excludes*
outputs — so "was this the same experiment?" stays answerable before comparing
results. Same manifest hash with different output hashes is a reproducibility
failure and should be treated as one.
