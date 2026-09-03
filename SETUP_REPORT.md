# Frozen capsule setup report

Setup date: 2026-08-31 (Asia/Shanghai)

## Outcome

All seven frozen task identities now have separate `original_task/`, complete
agent-facing `test_repo/`, reference, private qualification, scored-run, and
result surfaces. The run harness derives both conditions from the same
`test_repo/`, performs lock/leakage/state checks, supports frozen state-loss
snapshots, and archives the entire final repository separately from normalized
results. No scored RUN_MATRIX trajectory was executed or materialized.

The aggregate status is **QUALIFIED_WITH_BLOCKERS**: T1-T4 and T6 are qualified;
T5 and T7 are retained under their frozen identities and marked `BLOCKED` with
technical evidence. They were not replaced or silently simplified.

## Exact authoritative sources

| Task | Frozen authority and revision | Immutable task material |
|---|---|---|
| T1 `query-optimize` | `harbor-framework/terminal-bench` commit `624df069c505c5ddd21d2d78467dd5579020db95`, task tree `c04a867b98a03f27199ebd6c40d54a2f97d807ae` | Harbor digest `sha256:169496ea6843cb403b0860132675baf7aa0df0ac8b86221068e27d86395260f4`; OEWN SQLite SHA-256 `89eab7555b6b86a74b8e0ee5a7db7beec0b2575a45cd2b22fe132eae79f5ad5a` |
| T2 `gabeorlanski/dag_execution` | Official Harbor 0.22.0 SlopCodeBench payload; embedded source `4d38d30-dirty`, revision `v5` | `sha256:39aaaeea8576649f6defa53584f234d4873f2cdb8eea806123279909b57ff36c` |
| T3 `gabeorlanski/database_migration` | Same official source family/revision | `sha256:15a6ac32fc6e2ac000df7e634d6f21899aed228418fdb277725ee93790f0d25f` |
| T4 `gabeorlanski/recli` | Same official source family/revision | `sha256:5bbf98e020437d0dac4b74b5da803d4e0c6827540dca31ef26535f7e98209322` |
| T5 `rlMetaMazeMisc` | `facebookresearch/MLGym` commit `9d40c1b5035202018cd7091fb4e83a9c68b377c0`; authoritative `configs/tasks/rlMetaMaze.yaml` | Exact repository files at the pinned commit; unrelated historical trajectories were omitted only because their names exceed Windows path limits |
| T6 `capsule-4252248` | `siegelz/core-bench` commit `e32a2980e72fe6eb04ee04eb749458f570625663`; Code Ocean capsule v1 | Capsule tar SHA-256 `bd7a853f2f4859431848c52fcb9288edfbacac41e1b8b8fabc02179989471dd4`; restored image digest `sha256:cde83cedfb51150e20b442cd2f988f62f92864f8d661979c11f7f035c4b156f5` |
| T7 `sequential-neural-score-estimation` | `openai/frontier-evals` commit `51052cede8cc608f95bb00346635e03759013e5a` plus hydrated Git LFS | Paper PDF OID/SHA-256 `4161e45352ce3a8a247dce0841c2a90f0445653872b9616ca1954ebfaa81a57c` |

Per-task file counts, byte counts, content-tree hashes, source metadata,
qualification state, prompt hash, visibility-manifest hash, and runtime hash are
authoritative in each `TASK_SOURCE.json`/`TASK_LOCK.json` and the aggregate
`manifests/TASK_LOCK.json`. The host, image, and dependency facts are frozen in
`manifests/ENVIRONMENT_LOCK.json`.

## Capsule construction and visibility

`original_task/` preserves the complete relevant upstream setup and is never a
scored workspace. T7 includes both `project/paperbench` and its required
`project/common` sibling. `test_repo/` is a complete runnable repository,
contains the frozen task and resource policies, and owns the runtime directly
at its root. The Direct condition is copied from it with `.ai-workflow/`
physically omitted; there is no independent Direct project tree.

Official hidden tests, solutions, expected answers, future checkpoint prompts,
rubrics, and judge implementations were moved or copied to
`qualification/private_eval/`. Visibility is enumerated by each
`reference_material/VISIBILITY_MANIFEST.json`. T6 exposes its public source
paper citation and CC BY supplementary methods/figures; T7 exposes the paper,
addendum, blacklist, and official research assets. Private surfaces are never
mounted into the agent repository or container. Automated sensitive-material
and reference-policy checks run both during materialization and repository
validation.

The repository-default and seven initial `.ai-workflow/` trees are generated
copies of the configured clean v5.6.39 runtime. Their
state is `active_plan_id: null` and `plans: {}`; no task-specific Plan, Phase,
DIC, EPS, report, or history is pre-created. A representative runtime test run
under explicit UTF-8 mode passed all 19 focused v5.6.39 tests;
`python -X utf8` remains the locked Windows invocation.

To keep Git and operator uploads lean, those eight expanded trees are generated
and ignored. The complete `AI_Native_Workflow_v5.6.39/` package is tracked once
as the authority; `AI_WORKFLOW_RUNTIME.zip` is a canonical generated, ignored
archive. `scripts/sync_ai_workflow.py` deterministically builds/checks the
archive and installs byte-identical clean copies. `start_run.py` invokes the sync tool's `--ensure`
mode to restore missing copies while refusing to overwrite a differing existing
runtime without an explicit sync. For deliberate pre-run runtime maintenance,
`scripts/update_ai_workflow.py` loads the source configured by
`AI_WORKFLOW_RUNTIME_SOURCE.json` (currently
`AI_Native_Workflow_v5.6.39/.ai-workflow`), rebuilds the root archive,
synchronizes all copies, refreshes locks/manifests, and validates with rollback
of tracked metadata on failure.

## Technical adaptations

- T1 retains the native verifier and its raw output. A continuous score was
  added only after exact correctness, column/order, immutable-database,
  single-statement, and query-form gates pass. Semantic failure always scores
  zero. The optimization component uses the locked unoptimized/golden timing
  ratio and does not weaken the native correctness definition.
- T2-T4 preserve official cumulative tests, prior-test retention, and
  checkpoint counts. Only checkpoint 1 is initially visible. The reveal tool
  requires an accepted cumulative grader artifact and reveals exactly one next
  checkpoint. T3 and T4 enforce their frozen checkpoint state-loss boundaries.
- The Direct coding condition now launches the frozen coding CLI directly with the current task as
  an approved Goal; it uses zero Main inferences and no Main handoff ZIP. The AI-Native condition
  uses exactly one Main inference per currently revealed scope and requires one canonical whole-Phase
  ZIP containing the Phase manifest, every DIC view, the full initial EPS graph, one prompt file per
  EPS node, the Orchestrator entrypoint, and lineage metadata.
  `scripts/start_run.py` provides the one-command operator surface: it creates
  a UTC-stamped run folder and opens Direct immediately. Only AI-Native packages `MAIN_INPUT.zip`,
  references the source-derived repository-root `AI_WORKFLOW_RUNTIME.zip`, asks for the Main-chat
  link and `MAIN_HANDOFF.zip`, and imports the result before opening the executor in `workspace/`.
  Run/chat/executor timing, routing, usage, and hashes are consolidated in the
  evolving `RUN.json`; Main-chat token use remains uninferable from a saved
  URL. `scripts/generate_chat_main_runbooks.py` emits the concise per-task
  commands.
- T5 uses the exact starter, config, native evaluator, and held-out mean reward;
  its research extension asks for reproducible hypothesis-driven work without
  prescribing an algorithm. A compatible CUDA dependency lock was diagnosed
  and retained; no scientific mismatch was patched.
- T6 keeps the complete capsule in the workspace while isolating the expected
  answer and CORE-Bench harness. A deterministic private one-question wrapper
  emits the native correct-question count.
- T7 retains full PaperBench rather than Code-Dev. It mounts only official
  agent-visible paper material and presents an empty submission surface; the
  rubric and native judge are private.

## Qualification results

| Task | Status | Non-agent result |
|---|---|---|
| T1 | QUALIFIED | Seven golden executions passed all gates; native pass true; continuous oracle 100. Locked timings: unoptimized 344.385778 s, golden median 0.459976 s. |
| T2 | QUALIFIED (upstream caveat) | Checkpoint 3: 49 passed, 2 failed, core 3/3, isolated 10/10. The exact same two failures occur at official checkpoint 1, demonstrating a frozen reference defect rather than erosion. |
| T3 | QUALIFIED | Checkpoint 5: 136 passed, 1 skipped; core 3/3, isolated 20/20, strict 1.0. Both workspace conditions, reveal, state loss, and full final archival passed a qualification-only dry run. |
| T4 | QUALIFIED | Checkpoint 8: 255/255 passed; core 7/7, isolated 41/41, strict 1.0. |
| T5 | BLOCKED | The pinned CUDA stack detected the GPU and completed one full PPO seed/checkpoint. The authoritative config says 64 evaluation environments but the shipped evaluator hard-codes 256. |
| T6 | QUALIFIED | All three official R scripts exited 0 in the restored image; generated output reproduced `AUC = 0.4929241`; private native grader returned 1/1. |
| T7 | BLOCKED | Exact `uv.lock` sync succeeded (Python 3.11.15, 202 packages); both official images built; the root non-API unit suite passed 49/49 (18 API-judge cases deselected). Native judging and full target GPU execution remain unqualified. |

Raw evidence and exact caveats are in each task's
`qualification/QUALIFICATION_REPORT.md` and `oracle_runs/`; these setup checks
did not use ChatGPT, Claude, Codex, or Claude Code as candidate solvers.

## Frozen matched resource budgets

The same budget applies to Direct and AI-Native within each task. Full details,
including network and storage rules, are in the task's `RESOURCE_POLICY.md`.

| Task | Wall time | Main interactions | Executor time | Concurrent workers | GPU/training cap |
|---|---:|---:|---:|---:|---|
| T1 | 90 min | 60 | 60 min | 1 | no GPU |
| T2 | 4 h | 120 | 180 min | 2 | no GPU |
| T3 | 6 h | 160 | 240 min | 2 | no GPU |
| T4 | 8 h | 200 | 360 min | 2 | no GPU |
| T5 | 12 h | 240 | 480 min | 2 | max 8 GPU-h and 10 full training runs |
| T6 | 8 h | 160 | 240 min | 2 | no GPU unless capsule requires it |
| T7 | 24 h | 400 | 720 min | 2 | max 12 GPU-h and 6 full reproductions |

No cloud or API compute was purchased. T5-T7 use the same mixed model/research
resource menu in both conditions. T1-T4 require the exact product-visible model
families in the frozen protocol, with actual identifiers recorded at run time.

## Run harness and dry qualification

`scripts/prepare_run.py` lock-checks the source, rejects inherited runtime
state/caches, enforces condition-specific runtime presence, checks hidden and
reference leakage, and captures immutable source/task-lock and initial-tree
hashes. The simple operator layout avoids a duplicate `repo_initial/`; the full
final repository remains mandatory. `scripts/capture_state_loss.py` snapshots
the exact surviving repository while explicitly excluding transcript transfer.
`scripts/finalize_run.py` copies and hashes the entire final repository and
creates the separate native-result surface.

Qualification-only T3 Direct and AI-Native workspaces were created outside the
scored surfaces. Direct correctly omitted `.ai-workflow/`; AI-Native retained
it. Sequential checkpoint reveal, state loss, recovery record creation, and
entire-repository finalization succeeded. The final tree hashes were
`bf0bf1a2babe5a82763f72d2a5e1d652a021613c0abf379110ebb6abea17c307`
(Direct) and
`b2d86f5f58d67252d356cf4fe963e561b7b51c76368a11a064ac9213efb2c2d7`
(AI-Native). No valid Main handoff import, executor session, finalization, score, or executed
scored trajectory exists. An older Direct materialization is retained as
`INVALIDATED_PRE_TRAJECTORY`, and an operator-created AI-Native materialization
is retained at `AWAITING_MAIN`; both remain auditable without being treated as
completed trajectories. All `run_results/` surfaces remain empty of result IDs.

## AI-Native provenance and prompting audit

The prior v5.6.35 workflow source package remains immutable historical
provenance (SHA-256
`2df995c1eb3e0fc144e0e82555d96584d5b4bad108d916754a70ac6412873cb7`).
The operative pre-run runtime source is now the locally configured v5.6.36
package, which is tracked in full. The root runtime ZIP and eight expanded
runtime trees are reconstructed duplicates and intentionally ignored.
The machine-facing `.aiexplainer/` points to canonical runtime/specification
material, and the portable explainer ZIP is generated deterministically.
Runtime prompting/routing documents were audited against current official
OpenAI and Anthropic guidance. The source lock records URL, title, retrieval
date, and content hash without unnecessarily vendoring provider pages. This
global material is not exposed to Direct scored runs.

## Blockers and remaining manual actions

1. **T5/T5m:** obtain an authoritative resolution for the 64-versus-256
   evaluation-environment conflict, or issue an explicit protocol revision.
   Then repeat the native evaluator/oracle qualification and regenerate all
   locks. Do not patch the mismatch informally.
2. **T7/T7m:** an operator must supply the native grader credential through the
   approved secret mechanism, install/qualify NVIDIA Container Toolkit or move
   to a matched approved GPU host, and complete the full official PaperBench
   target qualification. Do not place secrets in this repository and do not
   downgrade the task to Code-Dev.
3. After either blocker changes, rerun the affected qualification, update
   `QUALIFICATION_STATUS.json`, regenerate task/environment locks, and run the
   complete final validation. No scored row for a blocked task may be started.

The exact human/Main loops for qualified Direct, AI-Native, progressive, and
state-loss runs are documented in `READY_FOR_SCORED_RUNS.md`.
