# Method: MCP Protocol Integration Patterns

**Domain:** Software Architecture / LLM Tooling
**Method type:** Emerging standard

## How It Works
MCP defines a client-server protocol where LLM agents (clients) discover and call
tools exposed by MCP servers. Servers expose a manifest of available tools with
JSON schemas for inputs/outputs. Transport can be stdio (local) or SSE (remote).

The key pattern: agents don't need to know tool implementations, only their schemas.
This decouples agent logic from tool logic.

## Why It Works
- Standardized tool interface across LLM providers
- Tool discovery is automatic (agents query the manifest)
- Composable: multiple MCP servers can be chained
- Transport-agnostic: works locally (stdio) or remotely (SSE)

## Why It Fails
- Specification is still evolving (breaking changes possible)
- Security model is immature (no fine-grained permissions yet)
- Performance overhead for high-frequency tool calls
- Limited error handling standardization

## When To Use
- Building agent systems that need to call external tools
- Integrating multiple AI providers with shared tooling
- Research orchestration (fan-out queries to multiple models/tools)

## Source
- https://modelcontextprotocol.io/
- https://github.com/modelcontextprotocol/specification

## Scores
- Confidence: 0.70 (emerging, not fully stable)
- Cost: 0.0 (open protocol, free implementations)
- Risk: 0.4 (specification changes may break integrations)
- Complexity: 0.5 (requires understanding of JSON-RPC and transport layers)
- Novelty: 0.8 (relatively new, adoption growing rapidly)
- Scalability: 0.7 (designed for distributed systems)
