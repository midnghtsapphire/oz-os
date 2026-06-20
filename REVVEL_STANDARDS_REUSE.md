# Oz OS → revvel-standards Reuse Assessment

**Question:** Can Oz OS (or other parts of the ecosystem) be used in `revvel-standards`?

**Short answer:** Yes — but selectively, and *by design*. Oz OS splits into two
classes of content. The **governance standards, schemas, and security findings**
are directly usable in `revvel-standards` and several of them describe fixes that
`revvel-standards` *needs*. The **research brain** (agents, research packs, intel
data, tool evals) should stay in Oz OS — merging it into the rulebook would
violate the architecture in `MISSION.md`.

---

## Scope & method

This assessment was produced from inside the Oz OS repo. `revvel-standards` was
**not directly accessible** in this session — only `midnghtsapphire/oz-os` and
`midnghtsapphire/risingaloha` are in scope, and `revvel-standards` returns
*"repository not configured for this session."* The picture of `revvel-standards`
below is reconstructed from the many references to it inside Oz OS:

| revvel-standards artifact | Referenced by |
|---|---|
| `wr/issues/**.md` (WR work-request tracker) | `wr-lint.yml`, `fix-wr-gate.yml`, README |
| `wr/scripts/wr-lint.mjs`, `wr/scripts/fix-wr-gate.mjs` | both workflows |
| `WR_TEMPLATE_FULL.md` (767 lines), `WR_TEMPLATE_BASIC.md` (65 lines) | INTEL-2026-001 |
| `learnings.md` (postmortems) | research-packs/github-actions |
| `research-orchestrator/mcp/manifest.json` | research-packs/mcp |
| `auto-merge.yml`, `pr-state-orchestrator.yml` | INTEL-2026-003 |

To turn this into a file-grounded migration (actual diffs against
`revvel-standards`), add `midnghtsapphire/revvel-standards` to the session scope
and re-run. Until then, the recommendations below are mapped to the artifacts
above rather than to exact line numbers.

---

## The architecture this has to respect

From `MISSION.md`:

> - `revvel-standards` = the rulebook (immutable, slow, reviewed)
> - `oz-os` = the brain (fast, append-only, agent-friendly)
> - Product repos = the output (consume intel, don't produce it)

"Reuse" therefore does **not** mean copying Oz OS into `revvel-standards`. It
means *promoting the standards-class content up* into the rulebook and *leaving
the fast-moving research content* in the brain. The test for each component:

> Is this a **rule/standard/schema** (slow, reviewed, governs other repos)?
> → it can live in `revvel-standards`.
> Is this **research output or agent machinery** (append-only, fast)?
> → it stays in Oz OS.

---

## Component-by-component verdict

| Oz OS component | Class | Usable in revvel-standards? | Action |
|---|---|---|---|
| `AUTONOMY_TIERS.md` | Governance standard | **Yes — high value** | Promote / adopt as the policy that governs revvel-standards' own auto-merge |
| `NULL_RESULT_SCHEMA.md` | Schema/standard | **Yes** | Promote as a shared standard |
| `intel/SCHEMA.md` | Schema/standard | **Yes** | Promote as a shared standard |
| `intel/INTEL-2026-002` (pull_request_target RCE) | Security finding | **Yes — actionable fix** | Audit & fix revvel-standards workflows |
| `intel/INTEL-2026-003` (auto-merge supply chain) | Security finding | **Yes — actionable fix** | Gate auto-merge with AUTONOMY_TIERS |
| `intel/INTEL-2026-005` (`gh` 1000-issue truncation) | Tooling finding | **Yes — actionable fix** | Paginate revvel-standards issue-scanning scripts |
| `intel/INTEL-2026-001` (WR template leakage) | Process finding | **Yes** | Already partly applied; finish defaulting to BASIC |
| `intel/INTEL-2026-004` (localStorage PAT) | Security finding | Indirect | Applies to product repos, not the rulebook |
| `.github/workflows/wr-lint.yml` + `fix-wr-gate.yml` | Shared CI | **Already revvel-standards' assets** | See "broken copies" below |
| `agents/*.md` (method-hunter, contrarian, …) | Brain | **No — keep in Oz OS** | Rulebook is slow/immutable; agents are fast |
| `research-packs/**` | Brain | **No — keep in Oz OS** | Append-only research, by design |
| `intel/` entries (the data) | Brain | **No — keep in Oz OS** | Append-only; only the *schema* is rulebook-class |
| `tool-intelligence/**` | Brain | **No — keep in Oz OS** | Evaluations, not standards |
| `method-packs/**` | Brain | **No — keep in Oz OS** | Methodology output |

---

## What is directly usable (port / adopt into revvel-standards)

### 1. `AUTONOMY_TIERS.md` — the single highest-value port
This is a pure governance standard (Tier 0 auto-merge → Tier 4 human + 24h
cooldown). It is *about* the exact problem `revvel-standards` has: per
`INTEL-2026-003`, `revvel-standards`'s `pr-state-orchestrator.yml` enables
auto-merge-on-CI-green with no quality gate beyond green — the root cause of the
"babysitting" / bad-WR-landing problem. `AUTONOMY_TIERS.md` is the policy that
closes that gap. It belongs in the rulebook and should be wired to
`revvel-standards`' branch-protection + auto-merge workflows.

### 2. The schemas — `NULL_RESULT_SCHEMA.md` and `intel/SCHEMA.md`
Schemas are definitionally rulebook-class (slow, reviewed, governs many repos).
`intel/SCHEMA.md` even has a "Why it matters → Impact on … revvel-standards"
field baked in. Promote both as shared standards that product repos and Oz OS
both validate against.

### 3. The security/tooling intel → concrete fixes in revvel-standards
Three intel entries don't just *inform* `revvel-standards` — they describe live
problems in its own automation:

- **INTEL-2026-002:** audit every `pull_request_target` workflow in
  `revvel-standards`; ensure none checks out PR head with secrets in scope.
- **INTEL-2026-003:** add a required `wr-lint`/tier check before auto-merge;
  quarantine agent PRs touching workflows/secrets/CI.
- **INTEL-2026-005:** any `revvel-standards` script that enumerates "all issues"
  must paginate — the repo is explicitly noted as approaching the 1000-issue
  truncation threshold.

These are the most immediately valuable use of Oz OS in `revvel-standards`:
the brain already did the research; the rulebook gets the fixes.

### 4. WR-template default (INTEL-2026-001) — finish the job
Default WR generation to `WR_TEMPLATE_BASIC.md`, reserve `WR_TEMPLATE_FULL.md`
for regulated work. Partly applied already; the standard should be codified in
the rulebook.

---

## What should NOT be merged into revvel-standards

`agents/`, `research-packs/`, `method-packs/`, `tool-intelligence/`, and the
`intel/` *entries themselves* are the "brain": fast, append-only, agent-authored.
Putting them behind the rulebook's slow/immutable review cadence would defeat the
whole point of the split (`MISSION.md`) and re-introduce the babysitting tax.
`revvel-standards` should **consume** these (cite intel, follow agent specs), not
**host** them.

---

## Bug found while assessing: broken workflow copies in Oz OS

`oz-os/.github/workflows/wr-lint.yml` and `fix-wr-gate.yml` invoke
`node wr/scripts/wr-lint.mjs` and `node wr/scripts/fix-wr-gate.mjs`, and trigger
on `wr/issues/**.md`. **None of those paths exist in Oz OS** — `wr/` is a
`revvel-standards` directory. These workflows are copies that were never adapted:

- On `revvel-standards` they are correct (that's their real home).
- In Oz OS they are dead — they only run when `wr/issues/**.md` changes, which
  never happens here, and would fail if it did (no scripts).

**Recommendation:** in Oz OS, either delete these two workflows or repoint them
at Oz OS's real validation surface (`intel/**.md`, `agents/**.md`) with an Oz OS
linter. Keep the canonical WR linter in `revvel-standards`. This confirms the
direction of reuse: WR tooling flows *from* `revvel-standards`, not into it.

---

## "Other parts": risingaloha → revvel-standards

`risingaloha/AGENTS.md` is a 9.6 KB **universal AI-agent instruction standard**
(prime directive, commit conventions, tech-stack defaults, security rules,
symlink fan-out to `CLAUDE.md`/`.cursorrules`/`GEMINI.md`/etc.). It is explicitly
written as org-wide ("MIDNGHTSAPPHIRE UNIVERSAL REPO INSTRUCTIONS"), yet it
currently lives in one product repo. That is exactly the kind of cross-repo
standard `revvel-standards` exists to own.

**Recommendation:** promote `AGENTS.md` to `revvel-standards` as the canonical
source, and have product repos (including `risingaloha`) pull/symlink it rather
than each carrying its own fork. The project-specific tail (the "Sessiono"
section) stays in `risingaloha`; the universal head becomes a standard.

---

## Recommended sequence

1. **Promote standards** into `revvel-standards`: `AUTONOMY_TIERS.md`,
   `NULL_RESULT_SCHEMA.md`, `intel/SCHEMA.md`, the universal head of `AGENTS.md`.
2. **Apply the security/tooling intel** as real fixes in `revvel-standards`
   workflows (INTEL-2026-002, -003, -005) and finish the WR-template default
   (INTEL-2026-001).
3. **Wire `AUTONOMY_TIERS.md` to enforcement**: required checks +
   branch-protection so tiers actually gate auto-merge.
4. **Clean up Oz OS**: fix or remove the misplaced `wr-*` workflows.
5. **Keep the brain in Oz OS**: agents, research/method packs, intel data, tool
   evals remain append-only here; `revvel-standards` consumes, never hosts them.

> Steps 1–3 require write access to `revvel-standards`, which this session does
> not have. Add `midnghtsapphire/revvel-standards` to the session scope to
> execute them as real PRs; this document is the plan they'd implement.
