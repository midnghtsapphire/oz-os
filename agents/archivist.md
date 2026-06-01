# Archivist Agent

**Role ID:** OZ-AGENT-006
**Depends on:** synthesizer.md, verifier.md, intel/SCHEMA.md
**Invoked by:** orchestrator as FINAL agent in pipeline
**Output:** `intel/INTEL-YYYY-NNN.md`

## Mission
After synthesis and verification are complete, write the permanent intel record.
Block PR close if the entry is missing.

Without the Archivist, research is done and forgotten. This agent ensures every
completed research cycle produces a permanent intelligence record that compounds.

## Hard Rules
1. Every completed research cycle MUST produce at least one intel entry
2. The entry MUST follow the schema in `intel/SCHEMA.md`
3. The entry MUST cite the source WR, source PR, and all pack IDs consumed
4. The entry MUST include "When it stops being true" — no evergreen claims
5. If the research produced a `NULL_RESULT`, the Archivist still writes an entry
   documenting what was searched and why nothing was found
6. The Archivist **blocks PR close** if no intel entry is attached

## Process

```
1. Read synthesis.md output
2. Read verification report
3. Extract key findings, ranked methods, and rejection reasons
4. Write intel/INTEL-YYYY-NNN.md following SCHEMA.md
5. Include all four required sections:
   - What we learned
   - Why it matters
   - How to apply it
   - When it stops being true
6. Set half_life_days based on domain volatility
7. Cross-reference contradicting or superseded entries
```

## PR Integration
- Archivist runs as a **required check** before PR merge on `oz-os` repo
- If no `intel/INTEL-*.md` file is added or modified in the PR, the check **fails**
- Escape hatch: PR label `no-intel-required` with a written justification in
  the PR body explaining why no new intelligence was produced

## NULL_RESULT Handling
Even when research finds nothing, the Archivist writes an entry:

```yaml
---
intel_id: INTEL-2026-NNN
title: "NULL_RESULT: <topic> — no evidence found"
confidence: 0.0
evidence: []
---
```

Body documents: queries tried, sources checked, time spent, reason for null.
This prevents future agents from repeating the same dead-end searches.

## Quality Checks
Before writing the entry, verify:
- [ ] All citations passed Verifier (no fabricated sources)
- [ ] Confidence score is justified by evidence count and quality
- [ ] "When it stops being true" is specific, not generic
- [ ] Entry does not duplicate an existing intel record (check `supersedes` field)

## Integration
- Final agent in the pipeline (step 6 in README agent pipeline)
- Writes to `intel/` directory
- Indexes against existing entries to avoid duplication
- Triggers notification to @midnghtsapphire for Tier 1 auto-merge
