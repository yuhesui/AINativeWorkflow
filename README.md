# AI-Native Workflow Internal Evaluation Repository — Frozen Protocol v1.0

This repository is the **internal experimental authority** for the frozen T1–T7 evaluation of AI-Native Workflow.
It may contain complete upstream task snapshots, private graders/oracles, source papers, raw trajectories, and experiment-only tooling. Do not publish it wholesale without license/canary/privacy review.

Current setup status: **QUALIFIED_WITH_BLOCKERS**. T1-T4 and T6 are qualified;
T5 and T7 remain frozen and `BLOCKED` for the exact reasons in
`SETUP_REPORT.md`. No scored trajectory is present.

## Task capsule invariant

Each `tasks/Txx_*` directory contains five distinct surfaces:

```text
tasks/Txx_name/
├── README.md
├── TASK_SOURCE.json
│
├── original_task/        # 1. complete untouched/minimally transformed upstream setup
│
├── test_repo/            # 2. actual complete repo opened during testing
│   ├── .ai-workflow/     #    AI-Native runtime at ACTUAL repo root
│   ├── TASK.md
│   └── ... task/project files ...
│
├── reference_material/   # 3. task papers/specs/supplements and provenance
├── qualification/        #    oracle/env/private evaluator/leakage qualification
│
├── runs/                 # 4. complete per-run subrepos; final repo state retained
└── run_results/          # 5. scores, graders, metrics, recovery summaries
```

### Which folder is actually tested?

**`test_repo/` is the scored repository root.**

For an AI-Native run, Main loads `test_repo/.ai-workflow/`, receives the frozen task prompt, and creates its own Plan → Phase → DIC → EPS state inside that repository.

For a Direct run, the harness materializes the same `test_repo/` while physically excluding `.ai-workflow/`. Direct never receives AI-Native files.

`original_task/` is the full upstream provenance copy, not the agent workspace.

## Global AI-Native references

Global workflow material lives under:

```text
reference_material/ai_native_workflow/
├── source_package/                         # full current AI-Native source ZIP
├── papers/                                 # technical report/workshop papers
├── .aiexplainer/                           # machine-facing read order + manifest
├── AI_NATIVE_WORKFLOW_FULL_AI_EXPLAINER.zip
└── prompting/                              # official prompting-source provenance
```

This material is retained for audit/context and is **not automatically exposed to Direct runs**.
Task-specific papers belong inside each task's `reference_material/` directory.

## Frozen tasks

- T1 — Terminal-Bench `query-optimize`
- T2 — SlopCodeBench `gabeorlanski/dag_execution`
- T3 — SlopCodeBench `gabeorlanski/database_migration`
- T4 — SlopCodeBench `gabeorlanski/recli`
- T5 — MLGym `rlMetaMazeMisc` (`configs/tasks/rlMetaMaze.yaml`)
- T6 — CORE-Bench Hard `capsule-4252248`
- T7 — PaperBench `sequential-neural-score-estimation`

Task identities, condition definitions, state-loss rules, and primary metrics are frozen by `EXPERIMENT_FREEZE.yaml`. Exact upstream revisions, hashes, container images, environment facts, qualification states, and matched resource budgets are locked in the task and manifest records.

## Setup versus scored runs

Setup/qualification may download tasks, run official oracles, validate environments, and dry-run harness code. It must not execute a scored Direct or AI-Native trajectory.
