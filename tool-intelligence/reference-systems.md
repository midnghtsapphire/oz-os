# Reference Systems

Systems Oz OS benchmarks against. These are not tools we use — they are systems
we study to understand design tradeoffs.

**Key insight:** Most of these optimize for **Answer Quality**. Oz OS optimizes
for **Method Discovery + Research Accumulation + Reusable Knowledge**. That
distinction drives every architectural decision.

---

## 1. NotebookLM (Google)

| Dimension | Assessment |
|-----------|-----------|
| **Optimizes for** | Source-grounded synthesis |
| **Ignores** | Multi-agent orchestration, adversarial review |
| **Oz OS borrows** | Source citation as a first-class concept |
| **Oz OS rejects** | Single-source-at-a-time limitation |
| **Feature to steal** | Audio overview generation from source material |

---

## 2. OpenHands

| Dimension | Assessment |
|-----------|-----------|
| **Optimizes for** | Agent execution with real tooling (browser, terminal, editor) |
| **Ignores** | Research accumulation, method diversity |
| **Oz OS borrows** | Tool-use architecture (agents that actually run code) |
| **Oz OS rejects** | Execution-first mindset (research should come first) |
| **Feature to steal** | Sandboxed execution environment for agent verification |

---

## 3. n8n

| Dimension | Assessment |
|-----------|-----------|
| **Optimizes for** | Workflow automation with AI nodes |
| **Ignores** | Intelligence compounding, research quality |
| **Oz OS borrows** | Visual workflow composition for non-technical users |
| **Oz OS rejects** | Treating AI as just another node in a pipeline |
| **Feature to steal** | Webhook-triggered workflows for event-driven research |

---

## 4. LangGraph

| Dimension | Assessment |
|-----------|-----------|
| **Optimizes for** | Multi-step agent orchestration with state management |
| **Ignores** | Adversarial review, null-result handling |
| **Oz OS borrows** | Graph-based agent orchestration patterns |
| **Oz OS rejects** | Implicit state management (Oz OS prefers explicit file artifacts) |
| **Feature to steal** | Checkpointing and human-in-the-loop interrupts |

---

## 5. CrewAI

| Dimension | Assessment |
|-----------|-----------|
| **Optimizes for** | Specialized agent teams with role assignment |
| **Ignores** | Evidence gating, method divergence |
| **Oz OS borrows** | Role-based agent specialization |
| **Oz OS rejects** | Agents that "agree" with each other (Oz OS agents are adversarial) |
| **Feature to steal** | Task delegation and sequential/parallel execution modes |

---

## 6. AutoGen (Microsoft)

| Dimension | Assessment |
|-----------|-----------|
| **Optimizes for** | Multi-agent conversations and debate |
| **Ignores** | Research persistence, intel accumulation |
| **Oz OS borrows** | Multi-agent debate as a quality mechanism |
| **Oz OS rejects** | Conversation as the primary artifact (Oz OS uses files) |
| **Feature to steal** | Code execution within agent conversations |

---

## 7. GraphRAG (Microsoft)

| Dimension | Assessment |
|-----------|-----------|
| **Optimizes for** | Knowledge graph + retrieval augmented generation |
| **Ignores** | Method discovery, contrarian analysis |
| **Oz OS borrows** | Knowledge graph structure for intel cross-referencing |
| **Oz OS rejects** | Automatic graph construction (Oz OS prefers human-verified intel) |
| **Feature to steal** | Community detection for finding related intel clusters |

---

## 8. Perplexity

| Dimension | Assessment |
|-----------|-----------|
| **Optimizes for** | Research-first retrieval with inline citations |
| **Ignores** | Method divergence, reusable knowledge packs |
| **Oz OS borrows** | Citation-as-evidence pattern |
| **Oz OS rejects** | Single-query-single-answer model (Oz OS requires 10+ methods) |
| **Feature to steal** | Source quality scoring and recency weighting |

---

## Summary Matrix

| System | Answer Quality | Method Discovery | Research Persistence | Adversarial Review |
|--------|:-:|:-:|:-:|:-:|
| NotebookLM | High | None | None | None |
| OpenHands | High | None | None | None |
| n8n | Medium | None | None | None |
| LangGraph | High | None | None | None |
| CrewAI | High | Low | None | None |
| AutoGen | High | Low | None | Medium |
| GraphRAG | High | None | Medium | None |
| Perplexity | High | Low | None | None |
| **Oz OS** | Medium | **High** | **High** | **High** |

Oz OS sacrifices raw answer quality to invest in method diversity, research
persistence, and adversarial review. The bet is that this compounds over time.
