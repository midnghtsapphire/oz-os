# Methods 3–4: Weave Characterisation and Sub-Pixel Registration

---

## Method 3 — Fourier Weave Characterisation

**Domain:** Texture analysis / signal processing
**Method type:** Academic

### How It Works

A periodic weave produces conjugate peaks in the 2D power spectrum. Peak radius
gives pitch, angle gives thread orientation, prominence gives regularity. The
region is mean-removed and Hann-windowed first, because a hard rectangular crop
produces cross-shaped spectral leakage that is easy to misread as a pair of
axis-aligned weave peaks.

Three guards make the detector honest, each added after it produced a false
positive during development:

1. **Minimum observed periods.** The search band excludes frequencies below
   `min_periods` cycles across the window (default 4). Periodicity is not
   established by one or two repeats.
2. **Local background.** Prominence is measured against an annulus at the peak's
   own radius, not a global median. Natural images are roughly `1/f`, so a global
   median is dominated by the high-frequency tail and makes low-frequency
   leakage look enormously significant — a smooth linear ramp scored `6.8 × 10⁹`
   under a global median.
3. **Strict radial local maximum.** Leakage from an aperiodic gradient decays
   monotonically with frequency (measured on a ramp: `2.3e0, 1.3e-1, 1.9e-2,
   4.4e-3`), so its in-band maximum sits at the band edge and is still rising
   inward. A real grating peaks and falls off on *both* sides (measured:
   `6.6e-1, 5.8e3, 2.2e4, 5.8e3, 6.7e-1`). Requiring a strict radial maximum
   accepts the second and rejects the first — prominence tests alone cannot.

### Why It Works

It measures the occluder as a material, which is a defensible claim: "the same
knit pitch and orientation appear in frame 3 and frame 11" rests on evidence
that is present in the pixels rather than absent from them.

### Why It Fails

- Stretch over a curved surface varies the local pitch, so a single global
  descriptor smears. Analyse per-patch and report the field.
- Below roughly 3 px pitch the weave aliases and the measured frequency is not
  the real one.
- Fine weave under JPEG compression is quantised away entirely.

### Source

- Reference implementation: `reference-impl/occlusion_forensics/weave.py`

### Scores

- Confidence: 0.85 | Cost: 0.0 | Risk: 0.45 | Complexity: 0.5 | Novelty: 0.3 | Scalability: 0.9

---

## Method 4 — Sub-Pixel Phase-Correlation Registration

**Domain:** Computational imaging
**Method type:** Industry-standard

### How It Works

Whiten the cross-power spectrum of two frames and inverse-transform; the peak
location is the displacement. Refine to sub-pixel accuracy by fitting a parabola
to the peak and its neighbours. Phase correlation is preferred over intensity
correlation because whitening makes it invariant to brightness and contrast
changes between frames — common when a subject moves between lighting zones or
auto-exposure adjusts mid-sequence.

### Why It Works

Registration to better than a pixel is the precondition for everything
multi-frame. Without it, fusion destroys detail instead of adding it, and the
coverage test computes the union of the wrong regions.

### Why It Fails — two traps worth naming

- **Windowing biases toward zero lag.** Applying an identical spatial taper to
  both inputs leaves a common envelope that survives whitening and correlates
  perfectly at zero displacement. Measured on aperiodic synthetic input, a Hann
  taper turned a clean `1.000` peak at the true shift into a `0.508` artefact at
  `(0, 0)` — beating the true peak at `0.314`. The reference implementation
  therefore defaults `window=False`, and a regression test pins the behaviour.
- **Periodic scenes are genuinely ambiguous.** A shift of one period is
  indistinguishable from none. This is a property of the scene, not a defect in
  the estimator. A low correlation peak on repetitive texture usually means
  ambiguity, not a small shift — check the peak, never the displacement alone.
- Translation-only. Rotation or scale change requires a log-polar extension.

### When To Use

Before coverage, always. Report the peak height alongside every shift.

### Source

- Reddy & Chatterji, IEEE TIP 1996
- Reference implementation: `reference-impl/occlusion_forensics/registration.py`

### Scores

- Confidence: 0.90 | Cost: 0.0 | Risk: 0.40 | Complexity: 0.5 | Novelty: 0.1 | Scalability: 0.9
