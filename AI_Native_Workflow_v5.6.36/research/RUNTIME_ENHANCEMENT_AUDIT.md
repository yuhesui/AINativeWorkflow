# Runtime Enhancement Audit — v5.6.36

## Scope

This audit covers the machine-facing `.ai-workflow/` runtime and the newly added submission/teaching preparation surfaces. It does not treat the outer development archive as operative project context.

## Binding architecture

```text
Main chat
→ optional Research / Theory / Experiment support
→ Main reconciliation
→ one whole-Phase DIC
   ├── README.md
   ├── REQUESTS.md
   └── PLAN.md (durable sequence, dependencies, parallelism, merge/repair graph)
→ coding-agent Orchestrator
→ JIT EPS attempts, model-tuned prompts, Workers/subagents, evidence
→ Verifier / Main reconciliation
```

## Corrections made

### Runtime boundary

- Only `.ai-workflow/` is identified as the installed runtime.
- Technical reports, research, submissions, slides, and provenance remain outer development storage.

### Main

- Main is explicitly a persistent user-facing planning and decision chat.
- Main plans one whole Phase and one multi-view DIC.
- Main does not expose a separate chat-level prompt graph or manage concrete EPS prompts.
- The compact Main table records Plan/Phase, M/T/E activation, Research status, one-DIC/core-view status, DIC topology summary, evidence target, human gate, and whole-Phase handoff.

### Research

- Research is an advisory decision-support route rather than an automatic mutation authority.
- Binding path: `Main → Research → Main reconciliation → DIC/execution`.
- Research, Theory, and Experiment are activated only where materially useful.

### DIC and EPS

- Exactly one DIC is permitted per Phase.
- Required Core DIC views are `README.md`, `REQUESTS.md`, and `PLAN.md`.
- `PLAN.md` owns the durable prompt/dependency graph, sequence, parallel groups, subagent branches, merge nodes, evidence gates, and repair/review branches.
- EPS remains a disposable JIT realization; several EPS attempts may bind to one unchanged DIC.

### Coding-agent Orchestrator

- Orchestrator is explicitly a repository-aware coding-agent session.
- Every generated EPS prompt must be adapted to the actual execution model/surface using official-provider-derived guidance.
- Broad omnibus prompts are split at dependency, expertise, evidence, write-ownership, parallelism, or failure-semantic boundaries.
- Each prompt normally has one primary outcome and one to three tightly coupled work packages.
- Subagents are considered actively but used only for independent, isolated, specialized, or truly parallel work.
- Parent integration and independent acceptance remain distinct from Worker completion.

## Source-guidance refresh

The runtime distills current official OpenAI and Anthropic guidance rather than vendoring full provider webpages. The source lock records URLs, applicability, and extracted operational consequences.

## Validation achieved

- Python runtime imports and compiles.
- One-DIC and Core-view invariants are tested.
- DIC graph cycles/missing dependencies are rejected.
- EPS-to-DIC hash/identity binding is recovered.
- All four verification outcomes are represented.
- Deterministic repair-to-accept trace succeeds.
- Declared dependency impact cone matches the expected four downstream nodes.
- Fresh-store recovery returns `ok=true` with no warnings.
- Machine-facing documentation and prompt-source locks are checked by tests.

## Remaining limitations

- This reference runtime is not a production concurrency server.
- It does not infer hidden read/write dependencies automatically.
- Model/surface prompt tuning is a normative Orchestrator requirement rather than an automatic provider API compiler.
- Semantic verifier correctness remains outside structural recovery.
- The controlled C0/C1/C2/C3 agent benchmark remains unexecuted.
