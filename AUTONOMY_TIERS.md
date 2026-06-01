# AUTONOMY_TIERS — What Ships Without Human Approval

## Purpose
Define what agents can merge without human review. This is the single biggest lever
against babysitting — right now everything needs human review, which means nothing moves.

---

## Tier 0 — Auto-merge (no human needed)
- Typo fixes
- Link rot repairs
- Dependency bumps with passing tests
- Formatting / whitespace normalization

**Approval:** CI green → auto-merge

---

## Tier 1 — Auto-merge with notification
- Documentation additions
- New `intel/INTEL-*.md` entries (following SCHEMA.md)
- Research pack updates (append-only)
- Method pack additions

**Approval:** CI green → auto-merge → notify @midnghtsapphire

---

## Tier 2 — Requires 1 agent review
- New agent specs (`agents/*.md`)
- New research packs (creation, not update)
- Tool intelligence entries
- Reference system evaluations

**Approval:** 1 agent review + CI green → merge

---

## Tier 3 — Requires human approval
- Schema changes (`intel/SCHEMA.md`, `NULL_RESULT_SCHEMA.md`)
- New standards
- Anything touching `MISSION.md`
- Autonomy tier changes (this file)

**Approval:** @midnghtsapphire approval required

---

## Tier 4 — Requires human approval + 24h cooldown
- Deleting research (any file removal from `research-packs/` or `intel/`)
- Deprecating agents
- Changing hard rules in MISSION.md
- Repository-level configuration changes

**Approval:** @midnghtsapphire approval + 24h waiting period

---

## Implementation
- Tiers enforced via GitHub Actions + branch protection rules
- Each PR must declare its tier in the PR body: `Tier: 0` through `Tier: 4`
- Mismatch between declared tier and actual file changes triggers a gate failure
- When in doubt, use the higher tier
