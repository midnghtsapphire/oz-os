# Methods 8–12: Provenance, Synthetic-Detail Detection, and the Rejected Method

---

## Method 8 — Enhancement-Chain / Synthetic-Detail Detection

**Domain:** Image forensics
**Method type:** Experimental (validated on a real case, see below)

### How It Works

When someone supplies several versions of "the same" image, establish whether
they are independent observations or one frame re-rendered, and whether any step
in the chain *added* detail rather than revealing it.

Three measurements, taken together:

1. **Registration.** Phase-correlate every frame against the first. Genuine
   time-separated frames show non-zero displacement somewhere in the scene.
   Displacement of `0.000 px` across a whole stack means one source frame.
2. **Edge energy vs. true high-frequency power.** Tenengrad measures
   mid-frequency edge contrast; the fraction of spectral power above ~0.25
   cycles/px measures genuine fine detail. Real optical improvement raises both.
3. **Noise.** Estimate `σ` per frame.

The diagnostic signature of a generative upscaler is **edge energy up while true
high-frequency power and noise go down**. Real detail arrives coupled to sensor
noise, because both are high-frequency and the optics cannot separate them.
Synthetic detail is clean — the model draws a crisp edge over content it does
not have, and denoises while doing it.

### Validated Measurement

Run on a supplied four-image "enhancement" set (single doorbell-camera frame,
649×531, identical JPEG quantisation tables, sequential file IDs):

| frame | registration vs f1 | corr peak | edge energy | HF power share | noise σ |
|-------|--------------------|-----------|-------------|----------------|---------|
| 1 | reference | 1.0000 | 1.1353 | 0.03836 | 0.00983 |
| 2 | dy −0.004, dx −0.003 | 0.7512 | 0.5070 | 0.01859 | 0.00574 |
| 3 | dy −0.008, dx −0.006 | 0.6739 | 0.3388 | 0.01237 | 0.00493 |
| 4 | dy −0.008, dx −0.006 | 0.5811 | 0.3784 | 0.00819 | 0.00380 |

Findings:

- **Zero displacement throughout.** Not a time sequence. One observation, so the
  coverage gate returns `n = 1` and multi-frame recovery is unavailable.
- **The chain runs backwards.** Frame 1 is the original and by far the sharpest;
  each subsequent "enhancement" destroyed information (edge energy 1.135 → 0.338).
- **Frame 4 shows the fabrication signature.** Against frame 3: edge energy
  **+11.7 %**, true HF power **−33.8 %**, noise **−22.8 %**. Structure was drawn
  that is not in the source. Frame 4 must not be used as evidence of anything.

### Why It Works

The coupling between fine detail and sensor noise is physical. Decoupling them —
sharper *and* cleaner — requires a source of detail other than the sensor, and
there is only one candidate.

### Why It Fails

- Aggressive denoising followed by conventional sharpening can mimic the
  signature without a generative model involved. The method detects "detail not
  from the sensor", which is the right question, but does not identify the tool.
- Requires the original for comparison. On a single supplied image it can raise
  suspicion via spectral flatness but cannot prove addition.

### Scores

- Confidence: 0.75 | Cost: 0.0 | Risk: 0.20 | Complexity: 0.4 | Novelty: 0.9 | Scalability: 0.8

---

## Methods 9 & 10 — PRNU and JPEG Provenance

**Method type:** Academic (9) / Industry-standard (10)

**PRNU** (photo-response non-uniformity) is a sensor's fixed multiplicative
noise fingerprint, unique per physical device. Correlating a frame's noise
residual against a reference fingerprint links image to camera. It answers
*which device* — a question with a real, publishable error rate — rather than
*which person*.
Fails on: heavy recompression, scaling, cropping without the geometry, and any
generative pass, all of which destroy the fingerprint.

**JPEG quantisation tables and DCT histograms** reveal recompression history and
splicing. Identical tables across a set (as in the case above) indicate a common
encoder; comb-like DCT histograms indicate double compression.
Fails on: format conversion, and any re-encode that normalises tables.

- 9 — Confidence: 0.85 | Cost: 0.2 | Risk: 0.30 | Complexity: 0.7 | Novelty: 0.3 | Scalability: 0.5
- 10 — Confidence: 0.80 | Cost: 0.0 | Risk: 0.25 | Complexity: 0.3 | Novelty: 0.2 | Scalability: 0.9

---

## Method 11 — Shape-From-Shading Relief Under Fabric

**Method type:** Academic — included with a low score, deliberately

Recovers surface relief from shading gradients, giving protrusion depth of
structure beneath stretched fabric. It measures *surface geometry of the
occluder*, which is a real object fully in view.

Fails on: unknown illumination (the bas-relief ambiguity means shape, light and
albedo trade off against each other and cannot be separated without
constraints), non-Lambertian fabric, and any compression that smooths the very
gradients it integrates. **It does not see through anything.** Relief of a
draped surface is not the geometry of what is under the drape, and the
temptation to treat it as such is why it is scored at 0.70 risk.

- Confidence: 0.45 | Cost: 0.1 | Risk: 0.70 | Complexity: 0.8 | Novelty: 0.5 | Scalability: 0.4

---

## Method 12 — Generative Inpainting / Face Frontalisation — **REJECTED**

**Method type:** Obvious, widely available, and wrong for this purpose

Documented here so the rejection carries a reason and survives the next person
who proposes it.

### How It Would Work

A diffusion or GAN prior conditioned on visible context synthesises plausible
content for the masked region; a frontalisation model then rotates the result to
a canonical pose.

### Why It Fails

It does not fail on quality — modern inpainting is excellent, and that is the
problem. It fails on **epistemics**:

1. The output is a sample from the prior, not an estimate from the data.
   Section "Method 5" shows the data constrains nothing in `ker(A)`. The detail
   in the output comes from the training distribution, so it resembles the
   *population*, not the subject.
2. It is not falsifiable and has no per-case error rate. Under *Daubert*, a
   technique with no known error rate applied to a specific individual does not
   survive cross-examination.
3. Frontalisation of a turned head compounds this: pose synthesis invents the
   occluded hemisphere as well.
4. The failure is silent and confident. A wrong reconstruction looks exactly as
   convincing as a right one, so downstream reviewers cannot catch it.

The harm is concrete: a synthetic face reads as evidence, and a plausible wrong
face puts a real person in an interview room.

### Verdict

Rejected for any evidentiary, investigative or identification purpose. There is
no parameter setting, prompt, or "forensic mode" that repairs the underlying
problem, because the problem is that the information is absent from the file.

Legitimate uses exist and are not this: artistic restoration, previsualisation,
and clearly-watermarked illustration where no one will mistake the output for a
measurement.

### Scores

- Confidence: 0.05 (as a forensic method) | Cost: 0.3 | Risk: **1.00** | Complexity: 0.7 | Novelty: 0.6 | Scalability: 0.9
