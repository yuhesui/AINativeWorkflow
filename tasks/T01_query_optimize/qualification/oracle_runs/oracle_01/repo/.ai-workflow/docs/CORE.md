# CORE.md — AI-Native Workflow v5.6.35 Normative Core

1. **Package state beats chat memory.** `.ai-workflow/STATE.json` and referenced package evidence are authoritative.
2. **Human governance is coarse.** Human approval occurs at Plan approval, periodic checkpoints, and material escalations—not per prompt.
3. **Machine execution stays rich.** A Phase may contain 10–100+ prompt/runs.
4. **One DIC package per Phase.** `DIC/README.md`, `REQUESTS.md`, and `PLAN.md` are required views of the same Phase contract. `ARCHITECTURE.md`, `TEST_MATRIX.md`, and custom views extend it when useful.
5. **`DIC/PLAN.md` is the durable execution graph.** It records prompt IDs, dependencies, parallel subagent batches, merges and conditional branches.
6. **EPS is disposable.** EPS instantiates planned nodes just in time; ordinary retries/repairs should not rewrite durable Phase intent.
7. **Roles are Main / Theory / Experiment.** Research and orchestration are capabilities. Legacy role names are compatibility aliases.
8. **Optional lanes are `off|auto|on`.** `minor`, `research`, `verification`, and `checkpoints` default to lazy `auto` unless a Phase deliberately overrides them.
9. **Reports are mandatory and compact.** `reports/` is flat, always present, and capped at 10 files by default. It contains human synthesis plus key merged raw results.
10. **Scientific claims follow evidence.** Planned/smoke/pilot/confirmatory evidence must remain distinguishable; no fabricated results, theorem novelty or human authorship.

See `PHASE_DIC_EPS_STRUCTURE.md` for the full layout and semantics.
