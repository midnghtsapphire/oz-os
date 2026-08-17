# Methods 1–2: Clarity Anchoring and Occluder Segmentation

---

## Method 1 — Tile Focus Operators (Clarity Anchoring)

**Domain:** Classical computer vision
**Method type:** Industry-standard

### How It Works

Before reasoning about content, measure *where the image carries detail at all*.
Three independent focus operators are applied over a non-overlapping tile grid:

- **Laplacian variance** — variance of the second derivative; high for in-focus
  texture, and also high for sensor noise.
- **Tenengrad** — mean squared Sobel gradient magnitude; total edge energy.
- **Brenner gradient** — squared difference at a two-pixel horizontal lag; the
  lag acts as a mild low-pass, making it notably noise-robust.

A tile is an **anchor** when at least 2 of 3 operators place it above a
per-metric quantile. Claims may be made about anchor tiles; soft tiles are not
evidence and the report must say so rather than quietly averaging them in.

### Why It Works

The operators disagree in useful, characterised ways — noise inflates Laplacian
variance but not Brenner, directional structure favours Tenengrad. Requiring
agreement makes the anchor decision robust to any single operator's known
weakness. Per-metric quantiles keep the threshold scale-free, so the same
parameters work on a bright daylight frame and a dim IR frame without retuning.

### Why It Fails

- A flat but perfectly focused region (clear sky, a painted wall) scores low.
  Absence of detail is not absence of focus, and the anchor mask conflates them.
- Tile size sets the scale of what counts as detail; too large and a small sharp
  feature is averaged away by its soft surroundings.
- Compression blocking artefacts register as edges and can inflate all three.

### When To Use

First, always. Its output bounds every later claim.

### Source

- Krotkov, "Focusing", IJCV 1988; Brenner et al., J. Histochem. Cytochem. 1976
- Reference implementation: `reference-impl/occlusion_forensics/clarity.py`

### Scores

- Confidence: 0.95 | Cost: 0.0 | Risk: 0.15 | Complexity: 0.2 | Novelty: 0.1 | Scalability: 0.9

---

## Method 2 — Structure-Tensor Orientation Coherence

**Domain:** Texture analysis
**Method type:** Academic

### How It Works

Form the gradient outer product `J = [[Ix², IxIy], [IxIy, Iy²]]`, smooth it at
scale `σ`, and take its eigenvalues `λ₁ ≥ λ₂ ≥ 0`. Coherence
`((λ₁ − λ₂)/(λ₁ + λ₂))²` is 1 where gradients agree on a direction and 0 where
they point every which way.

Woven and knitted fabric has strongly oriented, locally consistent gradient
structure. Skin does not. Thresholding coherence together with gradient energy
segments the occluder without any learned model — and, importantly, without any
notion of what a face looks like.

### Why It Works

It keys on a property of the *occluder as a material*, which is fully visible,
rather than on the absence of something behind it. The output is a statement
about where measurement is blocked, which is exactly what the coverage gate
(method 5) consumes.

### Why It Fails

- `σ` must exceed the weave pitch, or the tensor measures individual threads
  rather than the fabric.
- Hair, brickwork, foliage and fence slats are also coherent. This is a triage
  heuristic and is stated as one; defaults are tuned to over-exclude, because
  wrongly excluding a visible pixel costs coverage while wrongly including an
  occluded one corrupts a measurement.
- Smooth gradients are technically coherent, hence the paired energy threshold.

### When To Use

To produce the visibility mask that feeds coverage. Never to infer content.

### Source

- Bigün & Granlund, ICCV 1987; Weickert, *Anisotropic Diffusion in Image
  Processing*, 1998
- Reference implementation: `reference-impl/occlusion_forensics/occlusion.py`

### Scores

- Confidence: 0.90 | Cost: 0.0 | Risk: 0.30 | Complexity: 0.4 | Novelty: 0.2 | Scalability: 0.9
