# Intel Entry Schema

All intelligence records in `intel/` must follow this YAML frontmatter schema.

## Frontmatter

```yaml
---
intel_id: INTEL-2026-001
title: <short noun phrase>
date: 2026-06-01
source_wr: <WR ID that produced this>
source_pr: <PR # if any>
domain:
  - github-actions
  - sar
  - mcp
confidence: 0.85        # 0.0–1.0
evidence:
  - type: postmortem     # postmortem | doc | code | conversation | external
    ref: <URL or path>
contradicts: []          # optional: [INTEL-2025-042]
supersedes: []           # optional: [INTEL-2025-099]
half_life_days: 90       # when to re-verify
---
```

## Body Sections

Every intel entry must contain these four sections:

### What we learned
The core finding. One to three paragraphs. No speculation.

### Why it matters
Impact on Oz OS, revvel-standards, or product repos. Be specific.

### How to apply it
Concrete action items. Link to the agent spec, workflow, or standard
that should change based on this finding.

### When it stops being true
Conditions under which this intel expires or needs re-verification.
Every intel entry has a shelf life — no evergreen claims.

## Naming Convention
Files: `intel/INTEL-YYYY-NNN.md`
- `YYYY` = year
- `NNN` = sequential number within the year, zero-padded to 3 digits

## Validation
- wr-lint.mjs runs against intel entries
- Verifier agent (agents/verifier.md) checks all citations
- Archivist agent (agents/archivist.md) creates entries after each research cycle
