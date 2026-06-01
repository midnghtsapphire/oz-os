# oz-os

**Oz OS — Research Intelligence Operating System**

> Most agent systems optimize for Answer Quality.
> Oz OS optimizes for **Method Discovery + Research Accumulation + Reusable Knowledge**.

## Quick Start

Read [MISSION.md](./MISSION.md) first. Everything else follows from it.

## Structure

```
oz-os/
├── MISSION.md              — why this repo exists
├── AUTONOMY_TIERS.md       — what ships without human approval (Tier 0–4)
├── NULL_RESULT_SCHEMA.md   — how to declare "found nothing" honestly
├── agents/                 — agent specs (method-hunter, contrarian, etc.)
├── research-packs/         — per-topic research bundles
├── method-packs/           — reusable methodology templates
├── intel/                  — permanent intelligence records
│   └── SCHEMA.md           — YAML frontmatter schema for all entries
├── tool-intelligence/      — tool evaluations + reference system comparisons
└── .github/workflows/      — CI gates (wr-lint, fix-wr-gate)
```

## Agent Pipeline

```
(1) METHOD HUNTER    → method-pack.md       (find 10+ methods)
(2) CONTRARIAN       → contrarian-pack.md   (attack every method)
(3) ADJACENT DOMAIN  → adjacent-pack.md     (steal from other industries)
(4) SYNTHESIZER      → synthesis.md         (merge, rank, resolve conflicts)
(5) VERIFIER         → verification report  (check every citation)
(6) ARCHIVIST        → intel/INTEL-*.md     (write permanent record)
```

## Rules
- No raw tokens or bracket-placeholders reach `main`
- Evidence-Gated Autonomy: no research → no architecture → no code → no merge
- `NULL_RESULT` is valid; fake completion is not
- Every failure writes an intel entry before the PR closes

## Parent WR
See `revvel-standards/wr/issues/OZ-OS-001-parent-index.md` for the full vision
and children WR tracker.
