# Research Pack: GitHub Actions

**Pack ID:** RP-github-actions
**Created:** 2026-06-01
**Status:** Seed pack — needs full Method Hunter pass

## Topic Summary
GitHub Actions is the CI/CD and automation backbone for all MIDNGHTSAPPHIRE repos.
Multiple failures (runner mismatches, workflow security, auto-merge risks) have been
documented in `revvel-standards/learnings.md` but never systematically researched.

## Known Methods
1. Workflow debugging via `ACTIONS_RUNNER_DEBUG` — see `methods/workflow-debugging.md`

## Search Terms Used
- `github actions runner labels`
- `self hosted runners configuration`
- `github actions security best practices`
- `pull_request_target security`
- `github actions auto-merge risks`

## Derived Search Terms
- `workflow_run trigger`
- `merge queue configuration`
- `concurrency control github actions`
- `reusable workflows`
- `composite actions vs reusable workflows`

## Sources Consulted
- GitHub Actions documentation (docs.github.com/en/actions)
- GitHub Security Lab research papers
- revvel-standards/learnings.md postmortems
- INTEL-2026-002 (pull_request_target RCE risk)
- INTEL-2026-003 (auto-merge supply-chain risk)

## Related Intel
- INTEL-2026-002: pull_request_target + checkout PR head = RCE
- INTEL-2026-003: Auto-merge SQUASH on agent PRs = supply-chain risk
