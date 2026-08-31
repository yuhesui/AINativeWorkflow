# Codex XHigh — Populate and Qualify the Frozen AI-Native Workflow Evaluation Capsules

## Role

Act as the experiment-infrastructure engineer for the attached `AI_Native_Workflow_Eval_v1.0_Frozen_Internal` repository.

The scientific design is frozen. Your job is to download and pin the exact benchmark materials, build the complete task capsules, make the agent-facing test repositories reproducible, qualify all environments/graders, and finish the run harness.

Do **not** execute any scored Direct-versus-AI-Native trajectory.
Do **not** redesign task identities, state-loss rules, condition definitions, or primary metrics.

---

# 1. Read first

Read, in order:

1. `README.md`
2. `EXPERIMENT_FREEZE.yaml`
3. `protocol/00_PROTOCOL.md`
4. `protocol/01_CONDITIONS.md`
5. `protocol/02_STATE_LOSS.md`
6. `protocol/03_SCORING.md`
7. `protocol/04_MODEL_POLICY.md`
8. `protocol/05_ANALYSIS_PLAN.md`
9. `manifests/RUN_MATRIX.csv`
10. every `tasks/Txx_*/README.md`
11. every `tasks/Txx_*/TASK_SOURCE.json`

Treat the repository layout below as an execution contract.

---

# 2. Frozen tasks

Use exactly:

- **T1** — Terminal-Bench `query-optimize`
- **T2** — SlopCodeBench `gabeorlanski/dag_execution`
- **T3** — SlopCodeBench `gabeorlanski/database_migration`
- **T4** — SlopCodeBench `gabeorlanski/recli`
- **T5** — MLGym `rlMetaMazeMisc`, authoritative config `configs/tasks/rlMetaMaze.yaml`
- **T6** — CORE-Bench Hard `capsule-4252248`
- **T7** — PaperBench `sequential-neural-score-estimation`

No task may be replaced because it appears difficult or because historical/model results look weak.
A technically impossible task must be marked `BLOCKED` with evidence. Replacement requires an explicit protocol revision before any scored run.

---

# 3. Critical task-capsule structure

Every `tasks/Txx_*` directory must contain **five logically separate surfaces**:

```text
tasks/Txx_name/
├── README.md
├── TASK_SOURCE.json
├── TASK_LOCK.json                    # create/fill during setup
│
├── original_task/                    # (1) complete upstream task setup
│   └── ... frozen original files ...
│
├── test_repo/                        # (2) ACTUAL complete repo used in testing
│   ├── .ai-workflow/                 # AI-Native runtime at scored repo root
│   ├── TASK.md
│   ├── RESOURCE_POLICY.md
│   └── ... task/project files ...
│
├── reference_material/               # (3) papers/specs/supplements
│   ├── agent_visible/
│   ├── provenance_only/
│   └── README.md
│
├── qualification/                    # (3) qualification/evaluator material
│   ├── private_eval/
│   ├── oracle_runs/
│   ├── ENVIRONMENT.md
│   ├── LEAKAGE_AUDIT.md
│   └── QUALIFICATION_REPORT.md
│
├── runs/                             # (4) complete per-run repositories
│   └── <RUN_ID>/
│       ├── RUN.json
│       ├── repo_initial/             # optional full snapshot or immutable hash ref
│       ├── repo_final/               # REQUIRED full final scored repo
│       ├── main/
│       ├── executors/
│       ├── state_loss/
│       └── evidence/
│
└── run_results/                      # (5) scores/diagnostics, separate from repo
    └── <RUN_ID>/
        ├── SCORE.json
        ├── METRICS.json
        ├── GRADER_RAW.*
        ├── RECOVERY.json             # when applicable
        └── SUMMARY.md
```

Do not collapse these surfaces together.

---

# 4. Meaning of `original_task/`

`original_task/` is the complete frozen upstream benchmark/task setup.

It exists for:

- provenance;
- independent reproduction;
- license/source audit;
- reconstructing the minimally modified test repo;
- retaining official grader/oracle/reference material where upstream distributes them together.

Populate it from the authoritative upstream source at an immutable revision.

Preserve the original structure as closely as practical.
Do not edit upstream code in place merely to make the experiment easier.

If the upstream package contains hidden/reference material that must not be shown to an agent, it may remain in `original_task/`, because **`original_task/` is never the scored workspace**.

Record exact provenance and hashes in `TASK_SOURCE.json` and `TASK_LOCK.json`.

---

# 5. Meaning of `test_repo/` — most important rule

`test_repo/` is the **actual full, complete repository opened by Main and by Codex/Claude Code during the experiment**.

It is not a thin wrapper and not merely a task prompt directory.

Construct it by minimally adapting `original_task/` so that:

- the benchmark can be executed locally/reproducibly;
- hidden/private evaluator material is removed from the agent-visible repository;
- task instructions are frozen and unambiguous;
- normal visible tests/tools remain available;
- the repository has all files a competent agent legitimately needs;
- AI-Native `.ai-workflow/` exists **directly at this repository root**.

Example:

```text
tasks/T03_database_migration/test_repo/
├── .ai-workflow/
├── TASK.md
├── RESOURCE_POLICY.md
├── pyproject.toml
├── src/
├── tests/              # only tests legitimately agent-visible
└── ...
```

For a scored AI-Native run, this is the repo Main sees.

For a scored Direct run, the harness copies this same repo while physically excluding `.ai-workflow/`.

Do **not** maintain a separately hand-edited Direct project tree. The Direct and AI-Native conditions must originate from the same `test_repo/` contents except for AI-Native workflow files/state.

Do not pre-create task-specific Plan, Phase, DIC, EPS, or execution history. The starting runtime must be clean:

```json
{
  "active_plan_id": null,
  "plans": {}
}
```

Main creates all experiment-specific AI-Native state after the task begins.

---

# 6. Meaning of `reference_material/`

Every task must have a dedicated task-reference surface.

Use:

```text
reference_material/
├── agent_visible/
└── provenance_only/
```

## `agent_visible/`

Store papers, specifications, supplementary materials, documentation, datasets descriptions, or other references that the frozen benchmark legitimately gives to the agent.

Examples:

- T6 source paper/capsule documentation if official CORE-Bench exposes it;
- T7 PaperBench source paper and any officially agent-visible addendum/supplement;
- task specifications required by the benchmark.

These materials may be copied/mounted into `test_repo/` or otherwise exposed by the official task interface when appropriate.

## `provenance_only/`

Store source papers, upstream documentation, licenses, supplementary files, archived webpages, or explanatory artifacts retained for audit but **not automatically agent-visible**.

Visibility must follow official benchmark semantics, not convenience.

Create a manifest recording which reference files are agent-visible and why.

---

# 7. Global AI-Native reference material

The evaluation repository also contains:

```text
reference_material/ai_native_workflow/
├── source_package/
├── papers/
├── .aiexplainer/
├── AI_NATIVE_WORKFLOW_FULL_AI_EXPLAINER.zip
└── prompting/
```

Preserve this as the global AI-Native provenance/context surface.

## `source_package/`

Contains the complete current AI-Native Workflow package ZIP used to derive the evaluation runtime.

Do not mutate the archived source package.

## `papers/`

Store the current AI-Native Workflow technical report and relevant workshop-paper snapshots used to understand claims/design.

These papers are reference material, not scored results.

## `.aiexplainer/`

Machine-facing orientation/index layer.

Keep it concise and point it to authoritative runtime/specification materials. It is not an alternative canonical workflow definition.

## `AI_NATIVE_WORKFLOW_FULL_AI_EXPLAINER.zip`

Preserve/update this as a portable AI-readable explainer/reference bundle.

If additional authoritative machine-friendly explainer artifacts exist in the supplied AI-Native package, place them here and update `.aiexplainer/MANIFEST.yaml`.

## `prompting/`

Store source-lock/provenance information for current official OpenAI and Anthropic prompting/context-engineering guidance used by the workflow.

Do not expose this global reference directory to Direct scored runs unless a frozen task independently makes some artifact available.

---

# 8. Qualification and hidden evaluator material

Use each task's:

```text
qualification/
├── private_eval/
├── oracle_runs/
├── ENVIRONMENT.md
├── LEAKAGE_AUDIT.md
└── QUALIFICATION_REPORT.md
```

Store here:

- official hidden grader/verifier implementation when it must be isolated;
- oracle/reference execution artifacts;
- expected answers;
- hidden test suites;
- benchmark canaries;
- environment qualification logs;
- repeated oracle results;
- dependency/version diagnosis;
- leakage checks;
- hardware/runtime feasibility notes.

Nothing under `qualification/private_eval/` may be reachable from the scored agent repository/container.

Do not rely on a textual instruction such as “do not read this folder.” Physically isolate it.

---

# 9. Runs must retain the full final repository

This is an explicit experiment requirement.

Every completed or failed scored trajectory must retain the **full final state of the subrepository** under:

```text
runs/<RUN_ID>/repo_final/
```

Do not retain only:

- a Git diff;
- selected output files;
- the final answer;
- summary statistics.

For an AI-Native run, `repo_final/` must include the final mutated `.ai-workflow/`, including all durable Plan/Phase/DIC/EPS/report/evidence state generated during execution.

For a Direct run, `repo_final/` must contain the full final Direct project state and must not contain `.ai-workflow/`.

Also retain, where permitted:

```text
runs/<RUN_ID>/main/
runs/<RUN_ID>/executors/
runs/<RUN_ID>/state_loss/
runs/<RUN_ID>/evidence/
```

Preserve failed/interrupted trajectories rather than deleting them.

A rerun due to infrastructure failure must receive a new run/attempt identifier and explicit invalidation reason.

---

# 10. Run results live separately

Use:

```text
run_results/<RUN_ID>/
```

for the normalized/scored interpretation of the raw run.

Store at minimum:

- native primary benchmark score;
- normalized completion score where defined;
- checkpoint/subcomponent metrics;
- grader raw output;
- wall time/resource metrics when available;
- state-loss/recovery metrics when applicable;
- validity/infrastructure status;
- links/hashes to the corresponding `runs/<RUN_ID>/repo_final/` and evidence.

Never replace native metrics with a composite score.

---

# 11. Download and pin authoritative task material

For every T1–T7:

1. locate the authoritative upstream repository/dataset;
2. verify the exact task identity against the current frozen protocol;
3. choose an immutable commit/dataset revision;
4. download the complete official task setup into `original_task/`;
5. preserve licenses/notices;
6. calculate content hashes;
7. populate `TASK_SOURCE.json` and `TASK_LOCK.json`;
8. construct `test_repo/` from that frozen original;
9. separate evaluator-only material into `qualification/private_eval/`;
10. populate task `reference_material/`;
11. qualify the environment and grader without a candidate agent.

Prefer authoritative source repositories/datasets. Document any unavoidable mirror.

---

# 12. Task-specific setup

## T1 — Terminal-Bench `query-optimize`

Freeze the complete official task and verifier.

Construct the continuous T1 score without changing semantic correctness requirements. Semantic correctness must dominate optimization performance.

Retain raw native verifier outputs.

## T2 — SlopCodeBench `dag_execution`

Preserve the official progressive three-checkpoint structure and prior-test retention semantics.

Extract native checkpoint metrics including strict/core/isolated pass rates and erosion/regression diagnostics.

## T3 — SlopCodeBench `database_migration`

Preserve the official five-checkpoint progression and all cumulative requirements.

Implement the optional state-loss hook after checkpoint 3/5 and before checkpoint 4 reveal.

## T4 — SlopCodeBench `recli`

Preserve the official eight-checkpoint progression and all cumulative requirements.

Implement the optional state-loss hook after checkpoint 4/8 and before checkpoint 5 reveal.

## T5 — MLGym `rlMetaMazeMisc`

Freeze the exact task associated with `configs/tasks/rlMetaMaze.yaml`.

Preserve native baseline/training/evaluation semantics and held-out mean reward as the primary scientific metric.

The task-facing research extension may require hypothesis-driven investigation, literature use, negative-result retention, and reproducible reporting, but must not prescribe the scientific method/algorithm to discover.

Configure local GPU execution and freeze realistic compute/time budgets before scoring.

## T6 — CORE-Bench Hard `capsule-4252248`

Freeze the complete target capsule/task, task question, environment requirements, paper/reference material under the official visibility policy, and native grader.

Expected answers belong in private evaluator material.

## T7 — PaperBench `sequential-neural-score-estimation`

Freeze the complete PaperBench task, source paper and officially visible research material, environment, grader/rubric, and execution machinery.

Private grading rubric/reference answers must not appear inside `test_repo/`.

Attempt full PaperBench qualification first. If local resources make full execution infeasible, mark `BLOCKED` and report the exact technical bottleneck. Do not silently downgrade to Code-Dev.

---

# 13. Model policy

## T1–T4 OpenAI ecosystem

Main:

`ChatGPT GPT-5.6 Sol — highest reasoning setting actually exposed`

Executor:

`Codex GPT-5.6 Terra — xhigh`

## T1–T4 Anthropic ecosystem

Main:

`Claude Opus 5 — high`

Executor:

`Claude Code Sonnet 5 — high`

Record exact product-visible identifiers at run time. Do not silently substitute.

## T5–T7 mixed research routing

Both Direct and AI-Native receive the same available resource pool. Main chooses model/tool routing itself.

Target resource menu:

- Main's own reasoning;
- Codex Terra xhigh;
- Claude Code Sonnet 5 high;
- Claude Opus 5 high research/reasoning session;
- web / primary-literature research;
- local terminal / Python / CPU / GPU.

The harness records routing but does not prescribe which tool must solve which Phase.

---

# 14. AI-Native run interface

Do not automate Main into an API benchmark loop.

Intended scored interface:

```text
fresh Main chat
    ↓
AI-Native loader prompt
    ↓
Main reads test_repo/.ai-workflow/
    ↓
frozen task prompt
    ↓
Main treats task as approved Goal
    ↓
Main creates Plan
    ↓
Main determines Phase decomposition
    ↓
Main creates active Phase folder + DIC + EPS
    ↓
Main delegates bounded work to permitted executors/research models
    ↓
evidence returned
    ↓
accept / repair / replan / next Phase
```

Do not pre-impose the number of Phases.

---

# 15. Direct baseline

Direct must be competent rather than intentionally weak.

It may plan, create notes, delegate, research where permitted, test, revise and maintain its own ordinary artifacts.

The only structural restriction is that it does not receive AI-Native Workflow.

The run harness must create Direct by copying `test_repo/` while physically excluding `.ai-workflow/`.

---

# 16. State-loss implementation

Implement but do not execute the scored state-loss variants.

- T3m: after checkpoint 3/5, before checkpoint 4 reveal.
- T4m: after checkpoint 4/8, before checkpoint 5 reveal.
- T5m/T6m/T7m: first stable Main↔executor handoff after 50% of the frozen total run budget.

On loss:

1. preserve exact surviving run repository;
2. preserve filesystem/Git/generated files;
3. do not transfer old Main transcript;
4. start a fresh Main;
5. give only the original task prompt, surviving repo, same resource menu, and frozen recovery instruction.

For AI-Native, recovery must rely on the surviving `.ai-workflow/` durable state.

---

# 17. Prompting-source audit

Audit the embedded runtime guidance and refresh global provenance under:

```text
reference_material/ai_native_workflow/prompting/
```

against current official OpenAI and Anthropic guidance.

Keep the runtime's synthesized operational documents, such as:

- `.ai-workflow/docs/PROMPTING_CORE.md`
- `.ai-workflow/docs/GPT56_ROUTING.md`
- `.ai-workflow/docs/CODEX_EXECUTION.md`
- `.ai-workflow/docs/CLAUDE_EXECUTION.md`

Do not vendor full copyrighted provider webpages unnecessarily. Record source URL/title/retrieval date/hash or archival identifier where practical.

---

# 18. Keep seven clean runtime copies identical

At the initial pre-run state, every:

```text
tasks/Txx_*/test_repo/.ai-workflow/
```

must be byte-identical.

Remove caches/generated test debris.
Require:

```text
active_plan_id = null
plans = {}
```

Run the existing runtime tests from at least one representative `test_repo/`.
Current expected baseline: **55 tests pass**.

---

# 19. Complete run harness

Update `scripts/prepare_run.py` and supporting tools so a run can be materialized from `test_repo/`.

For `AI_NATIVE`:

- copy complete `test_repo/`, including `.ai-workflow/`.

For `DIRECT`:

- copy complete `test_repo/` except `.ai-workflow/`.

Add automated checks for:

- hidden evaluator leakage;
- expected-answer/reference-solution leakage;
- wrong task revision;
- dirty/inherited AI-Native state;
- Direct accidentally containing `.ai-workflow/`;
- AI-Native missing `.ai-workflow/`;
- task/reference visibility policy violations.

Add finalization tooling that copies the **entire final repository** into `runs/<RUN_ID>/repo_final/`, hashes it, and links the result record.

---

# 20. Non-scored qualification only

Qualify every task using official oracle/reference/environment procedures where available.

Demonstrate:

- build/install succeeds;
- task starts;
- grader runs;
- native score parses;
- expected reference/oracle behavior works;
- hidden evaluator is isolated;
- `test_repo/` contains all legitimate dependencies;
- Direct/AI-Native workspace materialization works;
- state-loss snapshots can be created/restored structurally.

Use repeated oracle qualification when cheap. For expensive research tasks, use only enough non-agent validation to establish infrastructure correctness.

Do not run ChatGPT/Claude/Codex/Claude Code as candidate solvers during qualification.

---

# 21. Resource budgets

Before declaring readiness, propose and freeze matched Direct/AI-Native budgets per task, including as relevant:

- wall time;
- Main interaction budget;
- executor time;
- allowed concurrent workers;
- GPU time;
- training-run budget;
- network policy;
- disk/storage.

Do not purchase cloud/API compute without human approval.

---

# 22. Final required outputs

Populate/finalize:

```text
tasks/*/original_task/
tasks/*/test_repo/
tasks/*/reference_material/
tasks/*/qualification/
tasks/*/TASK_SOURCE.json
tasks/*/TASK_LOCK.json

manifests/TASK_LOCK.json
manifests/ENVIRONMENT_LOCK.json
scripts/prepare_run.py
```

Add:

```text
READY_FOR_SCORED_RUNS.md
SETUP_REPORT.md
```

`READY_FOR_SCORED_RUNS.md` must explain the exact human/Main operational loop for Direct, AI-Native, and state-loss runs.

`SETUP_REPORT.md` must report exact upstream revisions, environment requirements, hashes, qualification outcomes, visibility rules, technical adaptations, blockers, and remaining manual actions.

---

# 23. Final validation

Run at minimum:

```text
python scripts/validate_repo.py
```

plus:

- AI-Native runtime tests;
- task-lock and environment-lock checks;
- Direct/AI-Native workspace leakage checks;
- grader/oracle qualification;
- seven-runtime tree-hash equality;
- clean-state validation;
- test `prepare_run.py` in both conditions using a non-scored dry materialization;
- test final-repository archival into a dummy/non-scored `runs/` entry.

No scored run may exist at completion.

---

# 24. Hard stop

Do not:

- execute any scored row of `RUN_MATRIX.csv`;
- compare Direct against AI-Native outcome quality;
- tune frozen prompts based on candidate-agent performance;
- alter task identities;
- expose private graders/solutions to agents;
- publish the internal evaluation repo;
- push benchmark-sensitive assets publicly;
- expose credentials;
- purchase compute;
- submit a paper;
- change canonical scientific claims.

Return the fully populated internal evaluation repository, `SETUP_REPORT.md`, and `READY_FOR_SCORED_RUNS.md`.
