# Checkpoint 5 Requests

- Validate optional `depends_on` positive-version arrays and enforce applied dependencies for single migrations.
- Scan JSON migration directories, reject duplicate/missing/future dependencies and cycles, and produce deterministic topological order.
- Add non-mutating `validate` and dependency-ordered `migrate-all` JSONL commands.
- Preserve checkpoints 1–4, including rollback-compatible history behavior, and retain concise wrapper evidence.
