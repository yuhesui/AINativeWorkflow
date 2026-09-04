# Checkpoint 4 Requests

- Add `rollback <database> [--to-version N | --count N]` with JSONL lifecycle events.
- Persist migration operations and explicit rollback operations in durable history, upgrading older `_migrations` tables safely.
- Automatically reverse supported schema, constraint, index, and column/data-migration operations in reverse order; reject transform/backfill migrations without explicit rollback operations.
- Keep every selected migration rollback transactional, remove history only after success, and preserve foreign-key integrity.
- Retain concise wrapper evidence and stop before unrevealed scope.
