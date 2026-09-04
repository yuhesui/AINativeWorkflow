# Checkpoint 3 Requests

- Implement and validate `add_foreign_key`, `drop_foreign_key`, `create_index`, `drop_index`, `add_check_constraint`, and `drop_check_constraint`.
- Enable SQLite foreign-key enforcement at each migration, validate source/referenced tables, columns, key compatibility, actions, existing data, and named constraint/index existence.
- Recreate tables transactionally for foreign-key/check changes while preserving supported columns, tool-managed constraints, and custom indexes.
- Preserve all checkpoint-1/2 behavior and record only successful migration versions.
- Retain concise wrapper test evidence and stop before any unrevealed checkpoint.
