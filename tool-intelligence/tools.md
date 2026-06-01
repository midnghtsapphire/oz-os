# Tool Intelligence Registry

Honest assessments of tools evaluated by the team. This file compounds over time —
knowing what tools do and don't do prevents repeated evaluations and bad decisions.

---

## Manus

```yaml
---
tool_id: TOOL-2026-001
name: Manus
category: [orchestration, agent-runtime]
evaluated: 2026-06-01
evaluator: @midnghtsapphire
confidence: 0.85
recommendation: research-only
---
```

### Strengths
- Excellent multi-step task orchestration
- Handles complex agentic workflows with multiple tool calls
- Good at breaking tasks into subtasks

### Weaknesses
- Vendor lock-in: proprietary runtime, no self-hosting
- Tracking insertion: unclear what telemetry is collected
- Indirect API routing: requests pass through Manus infrastructure
- No way to audit what the agent is doing in real time

### Use Cases
- Research and evaluation only
- Not for production runtime with sensitive data

### Recommendation
**Research only.** Do not use as production runtime. Evaluate outputs but do not
route production API calls through Manus infrastructure.

---

## Keploy

```yaml
---
tool_id: TOOL-2026-002
name: Keploy
category: [testing, api-regression]
evaluated: 2026-06-01
evaluator: @midnghtsapphire
confidence: 0.80
recommendation: keep
---
```

### Strengths
- API regression testing via traffic capture and replay
- Records real API calls and generates test cases automatically
- Low setup cost for backend API testing

### Weaknesses
- Not a complete Mabl replacement (no UI testing)
- Limited browser/frontend testing capabilities
- Replay fidelity depends on API determinism

### Use Cases
- Backend API regression testing
- Capturing production traffic patterns for test generation

### Recommendation
**Keep.** Use for backend API testing alongside existing test suites.

---

## Perplexity

```yaml
---
tool_id: TOOL-2026-003
name: Perplexity
category: [research, retrieval, search]
evaluated: 2026-06-01
evaluator: @midnghtsapphire
confidence: 0.85
recommendation: keep
---
```

### Strengths
- Research-first retrieval with built-in citation
- Good at finding academic papers, documentation, and technical references
- Faster than manual search for initial research phase

### Weaknesses
- API costs scale with query complexity
- No local deployment option
- Citation accuracy varies (Verifier agent should check all outputs)

### Use Cases
- Research agent backend for initial method discovery
- Citation-heavy research where source tracking matters

### Recommendation
**Keep.** Primary research tool for Method Hunter and Adjacent Domain agents.
All outputs must pass through Verifier agent.

---

## OpenRouter

```yaml
---
tool_id: TOOL-2026-004
name: OpenRouter
category: [llm-gateway, infrastructure]
evaluated: 2026-06-01
evaluator: @midnghtsapphire
confidence: 0.80
recommendation: keep
---
```

### Strengths
- Multi-model gateway: access multiple LLM providers through one API
- Cost optimization: route to cheapest model that meets quality threshold
- Fallback routing: automatic failover when a provider is down

### Weaknesses
- Single point of failure for all LLM calls if OpenRouter goes down
- Rate limits apply across all routed requests
- Adds a network hop (latency)

### Use Cases
- Primary LLM gateway for all agent operations
- Cost optimization across research agents

### Recommendation
**Keep.** Use as primary gateway with direct-API fallback configured for
critical paths. Monitor uptime and have per-provider API keys as backup.
