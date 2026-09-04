# Phase Requests and Acceptance

## RQ-001 — Checkpoint-1 CLI and migration contract

- Priority: `primary`
- [ ] Outcome: `migration_tool.py migrate <migration.json> <database.db>` implements the complete currently revealed checkpoint-1 contract.
- Acceptance: missing/invalid migration files and invalid migration schema fail with exit code 1 and descriptive stderr beginning with `Error:`; valid database paths are created on demand.
- Acceptance: migration schema enforces positive integer version, required description/operations structure, supported operation types, valid identifiers, supported SQLite type names, at-most-one primary key per created table, and valid `auto_increment` use.
- Acceptance: `create_table`, `add_column`, and `drop_column` execute in listed order, with identifiers safely quoted/validated and `PRAGMA foreign_keys = OFF` applied for migration work.
- Acceptance: stdout contains only the specified JSON Lines operation/migration events for normal/skip flows; already-applied versions emit the exact warning semantics to stderr and a `migration_skipped` event to stdout.
- Evidence: focused runtime cases plus final whole-checkpoint verification logs produced through `.evaluation/run_in_env.py`.
- Verifier: P04 must independently exercise representative success and failure paths and inspect final diff/state.

## RQ-002 — SQLite schema/data fidelity

- Priority: `supporting`
- [ ] Outcome: schema mutations preserve data and all supported column semantics needed by checkpoint 1.
- Acceptance: `create_table` produces the requested column types and supported flags/default expressions, including `INTEGER PRIMARY KEY AUTOINCREMENT` when requested.
- Acceptance: `add_column` rejects nonexistent tables and duplicate columns and produces the requested supported column definition where SQLite permits the operation under the checkpoint contract.
- Acceptance: recreate-based `drop_column` rejects nonexistent tables/columns, sole-column drops, and primary-key drops; for a valid drop it copies all remaining row data, reconstructs the remaining supported schema faithfully, drops the old table, and renames the replacement atomically enough that a failed migration does not get recorded as applied.
- Evidence: schema introspection plus inserted-row preservation tests before/after drop.
- Verifier: P02 and P04.

## RQ-003 — Migration tracking and failure integrity

- Priority: `supporting`
- [ ] Outcome: `_migrations` is initialized exactly as required and records only successfully completed migrations.
- Acceptance: versions are checked before operations; a repeated version performs no schema mutation and emits the required skip warning/event.
- Acceptance: successful migrations insert version/description once and emit `migration_complete` with the exact operation count.
- Acceptance: SQL/runtime failure exits 1 with descriptive stderr and does not falsely record the failed migration; previously committed database state is not silently corrupted by a later failed operation in the same migration.
- Evidence: repeat-version, multi-operation failure, and `_migrations` inspection cases.
- Verifier: P03 and P04.

## RQ-004 — Durable evidence and checkpoint boundary

- Priority: `supporting`
- [ ] Outcome: execution leaves compact workflow evidence sufficient to recover what was attempted, what passed/failed, and whether checkpoint 1 is verifier-accepted.
- Acceptance: failures/repairs are retained rather than rewritten as success; decisive commands/output are stored under the active Phase evidence/log/report surface.
- Acceptance: no unrevealed checkpoint is inspected or implemented before the external harness reveals it.
- Evidence: updated Phase summary/evidence manifest/runtime state plus P04 verifier disposition.
- Verifier: Orchestrator integration and P04.

## Failure representation

Any request may end `complete`, `partial`, `blocked`, `negative-result`, or `superseded`. A local defect triggers a bounded repair EPS; a material contract problem triggers `replan`/`escalate`. Do not force unsupported success.
