# NULL_RESULT_SCHEMA — How to Declare "Found Nothing" Honestly

## Purpose
`NULL_RESULT` is a valid and respected output. Fake completion is not.
An honest "I found nothing after 10 queries" is infinitely more valuable than
a fabricated "here are 5 methods" with hallucinated citations.

---

## Schema

```yaml
---
null_result_id: NR-2026-001
topic: <research topic>
agent: <which agent produced this>
date: 2026-06-01
parent_wr: <WR ID>
confidence_in_absence: 0.0–1.0
reason: no_evidence_exists | evidence_contradicts_premise | access_denied | time_exhausted | scope_too_narrow
---
```

## Required Fields

### 1. Queries Tried
Exact search strings used, **minimum 10**.

### 2. Sources Checked
Databases, APIs, repositories, forums consulted.

### 3. Time Spent
Wall-clock time the agent spent researching.

### 4. Confidence in Absence
- `0.0` — barely looked
- `0.5` — reasonable search, might have missed something
- `0.8` — thorough search, unlikely to find more
- `1.0` — exhaustive search across all known sources

### 5. Adjacent Searches
Derived queries attempted after initial queries failed.

### 6. Reason for Null
One of:
- **`no_evidence_exists`** — topic is genuinely unresearched
- **`evidence_contradicts_premise`** — the question itself is wrong
- **`access_denied`** — sources exist but are paywalled / classified
- **`time_exhausted`** — more time would likely yield results
- **`scope_too_narrow`** — broadening the query might help

---

## Anti-Pattern
A `NULL_RESULT` with fewer than 10 queries tried is not a null result — it is
quitting early. The agent must retry with broader terms before declaring null.

## Integration
- Archivist (agents/archivist.md) still writes an intel entry for NULL_RESULT research
- The intel entry documents what was searched and why nothing was found
- NULL_RESULT packs are indexed in `intel/` for future reuse — knowing what
  *doesn't exist* prevents future agents from repeating the same dead-end searches
