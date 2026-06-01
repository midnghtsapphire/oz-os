# Method: Workflow Debugging via Runner Debug Logging

**Domain:** DevOps / CI-CD
**Method type:** Industry-standard

## How It Works
Set the repository secret `ACTIONS_RUNNER_DEBUG` to `true` to enable verbose
runner diagnostic logging. This exposes step-level timing, environment variables
(masked), and internal runner state that is hidden in normal logs.

## Why It Works
Most GitHub Actions failures produce terse error messages. Debug logging surfaces
the runner's internal decision tree — which labels matched, which caches hit/missed,
and where the runner spent time. This cuts diagnosis time from hours to minutes.

## Why It Fails
- Debug logs are extremely verbose (10x normal log size)
- Secrets may leak in debug mode if not properly masked
- Debug mode cannot be enabled per-workflow; it applies to all runs
- Does not help with permission or token-scope issues

## When To Use
- Runner label mismatch errors
- Unexpected cache behavior
- Workflow timing investigations
- "Works locally, fails in CI" issues

## Source
- https://docs.github.com/en/actions/monitoring-and-troubleshooting-workflows/enabling-debug-logging

## Scores
- Confidence: 0.90 (documented by GitHub)
- Cost: 0.0 (free, built-in)
- Risk: 0.3 (secret leakage concern)
- Complexity: 0.1 (one secret to set)
- Novelty: 0.1 (well-known)
- Scalability: 0.9 (works on any runner)
