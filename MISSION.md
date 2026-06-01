# MISSION — Oz OS

## What This Is
Oz OS is a **Research Intelligence Operating System**.
It is not an agent framework. It is not a chatbot. It is not an answer engine.

## What Oz OS Optimizes For
- **Method Discovery** — finding fundamentally different ways to solve problems
- **Research Accumulation** — every research cycle produces permanent intelligence
- **Reusable Knowledge** — intel entries compound; future WRs reuse past research

## What Oz OS Does NOT Optimize For
- Answer Quality (that is a side effect, not the goal)
- Speed of first response
- Agent count or complexity
- Code output volume

## Philosophy

```
Research Deeply.
Remember Everything.
Reuse Relentlessly.
Build Deliberately.
Evolve Continuously.
Evidence Before Action.
```

## Relationship to Other Repos
- `revvel-standards` = the rulebook (immutable, slow, reviewed)
- `oz-os` = the brain (fast, append-only, agent-friendly)
- Product repos = the output (consume intel, don't produce it)

## The Compounding Asset
Five years from now, the most valuable asset will not be code. It will be:
- Research Packs
- Method Packs
- Search Paths
- Intel Records
- Lessons Learned

The code will get rewritten. The intelligence is what compounds.

## Hard Rules
1. No raw tokens or bracket-placeholders reach `main` — enforced by `wr-lint.mjs`
2. Fix-class WRs MUST modify the buggy file — enforced by `fix-wr-gate.mjs`
3. No agent merges its own PR
4. Evidence-Gated Autonomy: no research → no architecture → no code → no merge
5. Every failure writes an `intel.md` entry before the PR closes
6. `NULL_RESULT` is a valid output; fake completion is not

## Method Divergence Requirement
Before any solution is proposed, agents MUST produce a Method Pack with 10+
methodologies: obvious, industry-standard, academic, open-source, enterprise,
low-cost, historical, adjacent-domain, contrarian, experimental.

Scored by: confidence / cost / risk / complexity / novelty / scalability.
