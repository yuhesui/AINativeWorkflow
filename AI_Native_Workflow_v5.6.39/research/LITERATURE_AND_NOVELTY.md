# Literature and novelty synthesis

## Bottom line

Hierarchical planning, manager/worker agents, explicit plans, reflection, memory externalization, multi-agent role specialization, workflow search, and verifier calls all predate this package. None is defensibly novel alone. The candidate contribution is a package-resident execution protocol that makes **persistent intent, semantic refinement, bounded execution, evidence-gated verification, dependency-local repair, and upward replanning** one inspectable state machine with explicit human-governance timescales.

That positioning is a system and evaluation contribution. The formal results clarify its conditions and limits, but the present theorems draw on established ideas from contract composition, incremental computation, reliability/checkpointing, and partial observability. The paper should not claim a new general theory of hierarchical planning.

## Closest families

### Planning and decomposition

ReAct interleaves reasoning and action; Tree of Thoughts and Graph of Thoughts organize deliberation; ReWOO separates planning from observation; ADaPT decomposes only when needed; LATS combines search, action, and reflection. These methods primarily optimize within-task inference. They do not by themselves supply a durable, repository-resident authority graph that survives fresh sessions and distinguishes machine execution boundaries from periodic human governance.

### Hierarchical and multi-agent systems

CAMEL, AutoGen, AgentVerse, MetaGPT, and related manager/worker systems establish role-based compound agents. HiAgent and memory-management work address long-horizon context. The distinction here is not “agents can be hierarchical,” but the explicit refinement/evidence lineage and closed-loop invalidation semantics across a durable research package. This must be demonstrated empirically rather than asserted from terminology.

### Long-horizon benchmarks and failures

AgentBench, WebArena, GAIA, SWE-bench, OSWorld, τ-bench, and subsequent computer-use/software-engineering benchmarks show that success degrades on long, stateful, dependency-rich tasks and that end-state scores can hide unsupported completion. They motivate controlled variation in effective horizon and fault propagation. Benchmark difficulty alone does not isolate the proposed mechanism, so the experiment must match model, budget, prompts, and verifier inference.

### Context and persistent state

MemGPT and retrieval/memory systems externalize context; software agents also use repositories, issue state, and execution logs. Externalization is not automatically sufficient: the active context projection must contain all phase-relevant state, and evidence identifiers must remain resolvable. The package contributes an explicit semantic contract for that projection, not a new memory architecture.

### Verification and scalable oversight

Reflexion, process supervision, debate/recursive oversight, tool-use safety evaluations, and verifier-guided search motivate feedback loops. A verifier call is additional inference and can itself be wrong. The proposed experiments therefore separate hierarchy from verifier inference, measure false acceptance/rejection proxies, and compare C2 versus C3 at matched budgets.

### Automated harness and agent design

DSPy, prompt optimization, automated design of agentic systems, and workflow-search systems optimize prompts or agent graphs. AI Native Workflow is complementary: it specifies authority, refinement, evidence, recovery, and human checkpoints for executing and auditing a chosen harness. It should not claim to outperform search-based harness optimization without direct evidence.

### Hierarchical world models

LeCun's world-model agenda and later joint-embedding predictive work motivate multi-timescale abstraction and planning. The present runtime does not learn latent predictive states, does not implement JEPA objectives, and is not equivalent to hierarchical world-model planning. Any reference is conceptual motivation only.

## Defensible novelty statement

> We operationalize long-horizon agent management as a durable refinement-and-verification protocol: an approved Plan is refined into machine-managed Phases, durable intent contracts, disposable execution plans, and evidence-linked actions; verification closes the loop through local repair, upward replanning, or material escalation, while dependency declarations bound safe invalidation.

This remains provisional until a fresh literature audit and controlled evidence establish that the integrated mechanism is not already implemented and evaluated in a materially equivalent system.

## Claims explicitly excluded

The manuscripts must not say that hierarchy alone is new; that the runtime guarantees semantic truth; that evidence gates are sound; that local recovery is safe with undeclared dependencies; that model context can be omitted without a sufficiency assumption; or that current unit/smoke tests demonstrate superior language-agent performance.

## Primary-source bibliography map

The package bibliography includes primary papers for ReAct; Tree/Graph of Thoughts; ReWOO; ADaPT; LATS; CAMEL; AutoGen; AgentVerse; MetaGPT; MemGPT; Reflexion; AgentBench; WebArena; GAIA; SWE-bench; OSWorld; τ-bench; DSPy; process supervision; scalable oversight; automated agent design; and JEPA/world-model motivation. Before external submission, the bibliography audit script and checklist require title/author/venue/URL reconciliation against the official paper or proceedings page.
