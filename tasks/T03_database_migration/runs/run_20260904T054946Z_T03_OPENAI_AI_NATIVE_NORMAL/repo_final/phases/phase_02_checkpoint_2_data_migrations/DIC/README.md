# Checkpoint 2 — Data Migrations

## Primary aim

Extend the accepted checkpoint-1 SQLite migration CLI with only the revealed checkpoint-2 operations: `transform_data`, `migrate_column_data`, and `backfill_data`. Preserve all accepted checkpoint-1 behavior and execute every migration atomically.

## Authority

- Plan: `plan_t03_progressive_migrations`
- Phase: `phase_02_checkpoint_2_data_migrations`
- DIC: `dic_t03_checkpoint_2_data_migrations`, revision `1`
- Predecessor: checkpoint 1 is accepted in the visible checkpoint state.
- Scope: `TASK.md`, `CHECKPOINTS/01.md`, and currently revealed `CHECKPOINTS/02.md` only.

Checkpoint 3 and any later checkpoint are not authorized.

## Execution route

Codex CLI / `gpt-5.6-terra` / `xhigh`. Task build, test, and runtime commands use the frozen-environment wrapper. The earlier checkpoint-1 wrapper limitation remains retained as historical evidence; this Phase records its own actual commands and outcomes.
