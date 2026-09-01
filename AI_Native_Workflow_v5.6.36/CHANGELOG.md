# Changelog

## v5.6.36 — Main/Research/Orchestrator clarity and Education preparation

### Runtime semantics

- Clarified that Main is a persistent planning/decision chat and Orchestrator is a repository-aware coding-agent session.
- Kept exactly one multi-view DIC per Phase.
- Named the Core DIC views as `README.md`, `REQUESTS.md`, and `PLAN.md`.
- Confirmed that `DIC/PLAN.md` contains the durable sequence, dependencies, parallel subagents, merge nodes, and conditional review/repair branches.
- Kept EPS as a disposable JIT operational realization that may be regenerated after ordinary failure.

### Main

- Added a compact Main starter.
- Added a whole-Phase planning checklist table.
- Added explicit activation/status notation for Main/Theory/Experiment without requiring all three in every Phase.
- Added the optional `Main → Research → Main reconciliation` route.
- Removed any requirement for Main to expose a separate chat-level prompt graph or executor-model dashboard.

### Orchestrator and prompting

- Required model/surface tuning for every concrete EPS prompt.
- Added a bounded-prompt default: one primary outcome and normally one to three tightly coupled work packages.
- Added an omnibus-prompt split test and a counter-rule against command-level micro-prompts.
- Added explicit subagent planning, parallelism, disjoint-write, and parent-integration rules.
- Refreshed provider-derived guidance from current official OpenAI and Anthropic documentation.

### Artifacts

- Added the Who Verifies the Agents? demo submission and anonymous supplement.
- Added a `slides/` section and a NeurIPS 2026 Education Track slide/materials plan.
