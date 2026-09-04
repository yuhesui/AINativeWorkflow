# Checkpoint 2 Requests and Acceptance

## RQ-201 — Data operation contract

- Implement `transform_data`, `migrate_column_data`, and `backfill_data` alongside every checkpoint-1 operation.
- Validate each new operation's required object/string/identifier fields and reject unsupported/malformed operations with `Error:` stderr and exit code 1.
- Require referenced tables and columns to exist before mutation. SQL expressions remain SQLite expressions and receive normal descriptive SQLite failures when invalid.

## RQ-202 — Transformation semantics

- `transform_data` updates each listed target column in listed order with its SQLite expression.
- `migrate_column_data` copies `from_column` to `to_column`, overwriting target data; null source values use `default_value` when supplied and otherwise remain null.
- `backfill_data` assigns a constant or SQLite expression to its target column, optionally restricted by `where`.

## RQ-203 — Atomicity and cumulative compatibility

- All data and schema operations in one migration share the existing transaction. Any failed operation rolls back all prior operations in that migration and does not create a `_migrations` record.
- Existing create/add/drop/skip behavior and JSONL operation events remain available.

## RQ-204 — Evidence and boundary

- Preserve concise command/output evidence, test results, verifier disposition, and any non-wrapper limitation.
- Do not inspect or implement unrevealed checkpoints.
