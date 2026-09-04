# Checkpoint 1 — Basic Schema Migrations

## Primary Aim

Deliver a correct, robust CLI implementation for the **currently revealed checkpoint 1 only**: apply JSON-described `create_table`, `add_column`, and recreate-based `drop_column` migrations to SQLite, with migration tracking, JSONL events, descriptive failures, data preservation, and the exact CLI contract in `TASK.md` / `CHECKPOINTS/01.md`.

## Purpose and durable context

This is the first executable Phase of T03. The task repository is intentionally minimal and contains no implementation at Phase start. The evaluator state at authoring time is `.evaluation/CHECKPOINT_STATE.json` with `current_checkpoint: 1`, `accepted: []`, and `revealed: [1]`.

The wider Plan is progressive, but **no later checkpoint content is known or authorized here**. The external grader/harness is the gate. Preserve checkpoint-1 behavior and durable workflow evidence so the same executor can recover state if a later checkpoint is subsequently revealed.

## Authority

- Plan: `plan_t03_progressive_migrations`
- Phase: `phase_01_checkpoint_1_basic_schema`
- DIC: `dic_t03_checkpoint_1_basic_schema`
- DIC revision: `1`
- Frozen task binding: `T03` / `run_20260904T054946Z_T03_OPENAI_AI_NATIVE_NORMAL` / `ccf7875ad006be0113af87c7407260177a243b0968ad269651a54fb74391f7ea`
- Execution route: Codex CLI, requested product-visible model `gpt-5.6-terra`, effort `xhigh`.
- Exact approved scope: implement and verify only checkpoint 1 as described by root `TASK.md` and `CHECKPOINTS/01.md`.

This file, `REQUESTS.md`, and `PLAN.md` are the single durable Phase intent contract.

## Core workstreams

```text
Main:       active / authored DIC + initial EPS
Theory:     not needed
Experiment: not needed
Research:   not needed
```

External research cannot materially improve this locally specified implementation task, so it is excluded.

## Read order

1. `DIC/README.md`
2. `DIC/REQUESTS.md`
3. `DIC/PLAN.md`
4. `TASK.md` and `CHECKPOINTS/01.md`
5. `.evaluation/CHECKPOINT_STATE.json`
6. current EPS manifest and the prompt for the ready node

## Priority and salience

- **Primary:** observable checkpoint-1 correctness under the specified CLI, SQLite semantics, schema validation, migration tracking, and error/output contracts.
- **Supporting:** transaction safety, preservation of remaining schema/data during `drop_column`, defensive identifier handling, and regression tests that exercise contract edges.
- **Optional:** small implementation refactors only when they simplify correctness. No dependencies, frameworks, or generalized migration language are goals.

## Execution environment contract

The harness has already provisioned and started the frozen task environment. Begin substantive repository work immediately. Run task build/test/runtime commands only through:

```bash
python .evaluation/run_in_env.py exec-self -- <command>
```

Do not add Docker/WSL/daemon/socket/image/container/sidecar/model-route/general-environment preflight or operator-confirmation gates. If an actually required wrapper command fails, retry that exact wrapper command once and preserve both outputs; continue repository work not dependent on it, escalating only if the repeated failure blocks a current acceptance criterion.

## Progressive checkpoint gate

Checkpoint 1 is the only revealed scope. After this Phase's evidence is complete, do not inspect, infer, implement, or create contracts for an unrevealed checkpoint. A later harness reveal may be acted on only after `.evaluation/CHECKPOINT_STATE.json` and the corresponding checkpoint file make that scope available. Until then, stop at the external gate with durable state intact.

## Non-goals

- No behavior from unrevealed checkpoints.
- No benchmark/solution search or external research.
- No replacement of SQLite or the specified Python CLI surface.
- No task-code changes outside the migration tool and locally useful test fixtures/tests.
- No public release, credentials, paid services, destructive external actions, or evaluator-private material.

## Material stops

Return upward only for a changed Goal/acceptance contract, an irreconcilable checkpoint contradiction, unavailable authority, destructive/external action, credentials/private systems, public release, or a repeated required wrapper failure that truly prevents a current acceptance criterion. Ordinary code/test defects remain inside bounded EPS repair semantics.
