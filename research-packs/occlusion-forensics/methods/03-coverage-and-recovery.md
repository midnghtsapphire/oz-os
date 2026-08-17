# Methods 5–7: The Coverage Gate, Fusion, and Bounded Deblur

This file carries the pack's central argument. Methods 1–4 are supporting
measurement; this is the part that decides what may be reconstructed at all.

---

## Method 5 — Null-Space Coverage Test

**Domain:** Inverse problems / linear algebra
**Method type:** Contrarian (it is a gate, not a capability)

### How It Works

Model the observation as `y = Ax + n`, where `x` is the scene and `A` is what
the imaging chain did to it.

A masking operator is a **projection**: it multiplies a region by zero. Unlike a
blur, which attenuates frequencies but leaves them recoverable above the noise
floor, a projection has a non-trivial **null space** `ker(A)`. For any candidate
solution `x̂` and any `v ∈ ker(A)`, `A(x̂ + v) = Ax̂`. The measurement is
*identical*. The data therefore places no constraint whatsoever on the null-space
component, and infinitely many scenes fit equally well.

The test: register the frames, then count per pixel how many frames observed
that location unoccluded.

```
counts[p] = Σ_i  visible_i( warp_i(p) )
counts[p] >= 1  →  recoverable; recovery is a measurement
counts[p] == 0  →  in the null space; any value written is invention
```

### Why It Works

It converts an argument people have opinions about into an integer they can
check. The gate is computed from observation geometry alone, *before* any
reconstruction exists to be admired, so the decision cannot be rationalised
after the fact by how good the output looks.

It also identifies the genuine escape route rather than only forbidding things.
If the occluder **moves relative to the scene**, different frames annihilate
different subspaces, and `∪ᵢ range(Aᵢ)` may cover everything. Then recovery is
honest, deterministic, and carries per-pixel provenance.

### Why It Fails

- It assumes registration succeeded. A mis-registered frame contributes coverage
  at the wrong coordinates and manufactures false confidence. Always check the
  correlation peak and the fusion dispersion together.
- It is binary per pixel and says nothing about *quality*. A pixel observed once
  through heavy motion blur counts the same as one observed sharply. Pair it with
  the clarity map (method 1) rather than reading coverage alone.
- Coverage of 1 permits recovery but offers no redundancy: that pixel's noise is
  whatever its single contributing frame had.

### The Compressed-Sensing Objection, Answered

The standard rebuttal is that compressed sensing recovers null-space content.
It does — under two conditions: the signal must be sparse in some basis, and the
measurement operator must satisfy a **restricted isometry property**, meaning the
measurements are incoherent with the sparsity basis and spread information
broadly.

A contiguous physical occluder is the worst case for RIP. The loss is spatially
coherent, structured and localised — the opposite of the incoherent sampling CS
requires. The guarantees do not transfer, and invoking CS to justify filling a
mask is citing a theorem outside its hypotheses.

### When To Use

Always, before any reconstruction. It is cheap and it is the difference between
an instrument and a generator.

### Source

- Candès & Tao, restricted isometry property, IEEE TIT 2005
- Reference implementation: `reference-impl/occlusion_forensics/coverage.py`
- Tests that enforce it: `tests/test_coverage_and_recovery.py`

### Scores

- Confidence: 0.98 — it is linear algebra, not a heuristic
- Cost: 0.0
- Risk: 0.05 — the failure mode is refusing too much, which is survivable
- Complexity: 0.3
- Novelty: 0.8 — the maths is old; making it a *mandatory gate* is the contribution
- Scalability: 1.0

---

## Method 6 — Multi-Frame Fusion and Iterative Back-Projection

**Domain:** Computational imaging
**Method type:** Industry-standard

### How It Works

Where coverage permits, register frames to sub-pixel accuracy, discard occluded
pixels, and average the survivors. Averaging is the maximum-likelihood
combination under independent Gaussian noise, giving the familiar `√N`
improvement. Iterative back-projection then refines: simulate what each frame
should have observed given the current estimate, take the residual against what
it *did* observe, and correct. Repeated, this recovers detail that sub-pixel
frame offsets encode but plain averaging blurs.

### Why It Works

Sub-pixel offsets between frames are genuine extra samples of the same
continuous scene. The information is really present; fusion is interpolation
between real measurements, not extrapolation into absence.

Critically, IBP **cannot create support**: a residual can only be computed where
an observation exists. The null space is untouched by construction rather than
by a guard someone could forget to write.

### Why It Fails

- Registration error converts directly into ringing and false edges. Under-relax
  the update step.
- It assumes a static scene. A subject that moves *non-rigidly* between frames
  violates the model, and the fused result is a blend of poses that resembles
  neither. Per-pixel dispersion across contributors flags this.
- Diminishing returns past roughly 8–16 frames for typical noise levels.

### When To Use

Only downstream of a coverage report that licensed it.

### Source

- Irani & Peleg, CVGIP: Graphical Models and Image Processing, 1991
- Reference implementation: `reference-impl/occlusion_forensics/recovery.py`

### Scores

- Confidence: 0.85 | Cost: 0.1 | Risk: 0.35 | Complexity: 0.6 | Novelty: 0.2 | Scalability: 0.7

---

## Method 7 — Wiener Deconvolution With a Measured Noise Floor

**Domain:** Signal processing
**Method type:** Industry-standard

### How It Works

The Wiener filter `H*/(|H|² + NSR)` is the minimum-mean-squared-error linear
inverse of a known blur. The NSR term is the important part: it automatically
stops amplifying each frequency once blur has pushed it below the noise. Estimate
the noise robustly first (MAD of a Laplacian response, per Immerkaer), then
report the frequency at which `|H|²` falls to the NSR — the highest frequency at
which any real recovery occurred.

### Why It Works

This is Case 1 of the governing result: attenuation, not annihilation. The
information survives in the measurement, merely suppressed, and inversion
recovers it with a computable bound.

### Why It Fails

- Requires a known or well-estimated PSF. A wrong kernel produces confident,
  structured artefacts that look like detail.
- Below the noise floor it recovers nothing, and any apparent detail there is
  amplified noise. **A deblur result quoted without its cutoff frequency is not a
  measurement** — that number is the whole claim.
- Assumes spatially invariant blur. Motion blur on a moving subject is not.

### When To Use

Where the degradation is genuinely a blur. Never as a substitute for coverage.

### Source

- Immerkaer, "Fast noise variance estimation", CVIU 1996
- Reference implementation: `reference-impl/occlusion_forensics/deblur.py`

### Scores

- Confidence: 0.90 | Cost: 0.0 | Risk: 0.40 | Complexity: 0.4 | Novelty: 0.1 | Scalability: 0.9
