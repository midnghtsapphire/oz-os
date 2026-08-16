# Research Pack: Occlusion Forensics

**Pack ID:** RP-occlusion-forensics
**Created:** 2026-08-16
**Status:** Method Hunter pass complete; reference implementation shipped and tested

## Topic Summary

What can be determined, deterministically and defensibly, from imagery in which
part of the subject is physically blocked from the sensor — and what provably
cannot.

The pack exists because the two halves of that question have different answers
and are routinely conflated. Measuring an occluder, locating detail, deblurring
within the noise floor, and fusing genuinely independent observations are all
well-posed. Recovering what the occluder hid is not — it is not a hard problem,
it is an ill-posed one, and no amount of compute changes that. See
`methods/03-coverage-and-recovery.md` for the argument and
`intel/NR-2026-001.md` for the null result.

## The Governing Result

Model the observation as `y = Ax + n`.

- When `A` **attenuates** (blur, downsample), inversion is legitimate down to
  the noise floor, with a computable error bound. Wiener/Tikhonov/TV live here.
- When `A` **annihilates** (a mask is a projection), `A` has a non-trivial null
  space. The data constrains nothing about the component of `x` in `ker(A)`.
  Infinitely many images satisfy the measurement exactly and equally well.
- Compressed sensing recovers null-space content only under sparsity **and** a
  restricted isometry property. A contiguous physical occluder is coherent,
  structured loss and violates RIP by construction, so the guarantees do not
  transfer.
- **The one exception:** if the occluder moves relative to the scene across
  frames, different frames annihilate different subspaces and the union of
  observations may cover the whole. That is measurable *in advance* — count
  per-pixel observations across registered frames. Covered → recover. Not
  covered → report insufficient and stop.

The reference implementation makes that gate structural rather than advisory:
`recovery.py` writes NaN wherever coverage is zero, and no parameter changes it.

## Method Divergence — 12 methods scored

Scores are 0.0–1.0. **Confidence** = how well established; **Risk** = chance of
producing a misleading result in careless hands.

| # | Method | Class | Conf. | Cost | Risk | Cplx. | Novelty | Scale |
|---|--------|-------|-------|------|------|-------|---------|-------|
| 1 | Tile focus operators (Laplacian var / Tenengrad / Brenner) | industry-standard | 0.95 | 0.0 | 0.15 | 0.2 | 0.1 | 0.9 |
| 2 | Structure-tensor orientation coherence | academic | 0.90 | 0.0 | 0.30 | 0.4 | 0.2 | 0.9 |
| 3 | Fourier weave characterisation | academic | 0.85 | 0.0 | 0.45 | 0.5 | 0.3 | 0.9 |
| 4 | Sub-pixel phase-correlation registration | industry-standard | 0.90 | 0.0 | 0.40 | 0.5 | 0.1 | 0.9 |
| 5 | **Null-space coverage test** | contrarian | 0.98 | 0.0 | 0.05 | 0.3 | 0.8 | 1.0 |
| 6 | Multi-frame fusion + iterative back-projection | industry-standard | 0.85 | 0.1 | 0.35 | 0.6 | 0.2 | 0.7 |
| 7 | Wiener deconvolution with measured noise floor | industry-standard | 0.90 | 0.0 | 0.40 | 0.4 | 0.1 | 0.9 |
| 8 | Enhancement-chain / synthetic-detail detection | experimental | 0.75 | 0.0 | 0.20 | 0.4 | 0.9 | 0.8 |
| 9 | PRNU sensor-noise provenance | academic | 0.85 | 0.2 | 0.30 | 0.7 | 0.3 | 0.5 |
| 10 | JPEG quantisation-table / DCT provenance | industry-standard | 0.80 | 0.0 | 0.25 | 0.3 | 0.2 | 0.9 |
| 11 | Shape-from-shading relief under fabric | academic | 0.45 | 0.1 | 0.70 | 0.8 | 0.5 | 0.4 |
| 12 | Generative inpainting / face frontalisation | **rejected** | 0.05 | 0.3 | 1.00 | 0.7 | 0.6 | 0.9 |

Method 12 is documented precisely so that it stays rejected with a reason
attached. See `methods/04-rejected-and-provenance.md`.

## Contents

```
occlusion-forensics/
├── README.md                    — this file
├── NON_GOALS.md                 — what the pack will not build, and why
├── methods/
│   ├── 01-clarity-anchoring.md          — methods 1, 2
│   ├── 02-material-and-registration.md  — methods 3, 4
│   ├── 03-coverage-and-recovery.md      — methods 5, 6, 7  (the core argument)
│   └── 04-rejected-and-provenance.md    — methods 8–12
└── reference-impl/              — working, tested Python (43 tests)
```

## Search Terms Used

- `deterministic image forensics occlusion`
- `null space masking operator inverse problem`
- `restricted isometry property structured occlusion`
- `multi-frame super resolution POCS iterative back projection`
- `phase correlation subpixel registration`
- `structure tensor orientation coherence texture segmentation`
- `PRNU sensor pattern noise camera identification`
- `Daubert standard image enhancement admissibility`
- `face frontalization occluded reconstruction limits`
- `super resolution hallucination artefact detection`
- `DeepMMSearch-R1 multimodal web search grounding crop`

## Derived Search Terms

- `error rate facial reconstruction forensic testimony`
- `ISO/IEC 19794-5 facial image resolution requirement`
- `upscaler detection high frequency power spectrum`
- `compressed sensing coherent measurement failure`

## Sources Consulted

- DeepMMSearch-R1, Narayan et al., arXiv:2510.12801 (ICLR 2026 under review) —
  establishes that current multimodal search agents *retrieve*; none reconstruct.
- Lukáš, Fridrich & Goljan, "Digital camera identification from sensor pattern
  noise", IEEE TIFS 2006 — the PRNU method.
- Reddy & Chatterji, "An FFT-based technique for translation, rotation and
  scale-invariant image registration", IEEE TIP 1996.
- Candès & Tao on restricted isometry; the RIP conditions method 5 relies on.
- Irani & Peleg, "Improving resolution by image registration", CVGIP 1991 — IBP.

## Related Intel

- `intel/INTEL-2026-006.md` — the coverage gate as a reusable design pattern
- `intel/NR-2026-001.md` — NULL_RESULT: no deterministic occluded-face recovery
