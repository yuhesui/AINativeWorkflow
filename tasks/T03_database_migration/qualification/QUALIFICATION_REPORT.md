# Qualification report

Status: **QUALIFIED**


The official checkpoint-5 oracle produced 136 passed and 1 skipped, with core
3/3, isolated 20/20, and strict pass rate 1.0.  A non-scored dry run verified
both condition workspaces, sequential checkpoint reveal, exact state-loss
snapshot after checkpoint 3 and before checkpoint 4, transcript exclusion,
and archival of each entire final repository plus separate result records.
No directory was added to the scored `runs/` or `run_results/` surfaces.

## 2026-09-04 environment requalification

The moving upstream `npm@latest` dependency became incompatible with its pinned
Node 22.12.0. A non-scored, non-agent requalification built the isolated adapted
Dockerfile as `ai-native-eval-t03:409fe6a21737` (image ID
`sha256:dba61c77a29fd97e740f99e213945d3dab9e1b18c1f2a5ebac22ae6257f24ecf`).
Inside the mounted `/app` sidecar, Node reported `v22.12.0`, npm reported
`10.9.0`, Python reported `3.12.14`, and `TASK.md` was present. The Direct Codex
launch was separately dry-resolved with Codex CLI `0.152.1`; no candidate solver
was started. Regression tests also verified that a pre-executor infrastructure
failure is marked `INVALID_INFRASTRUCTURE` and is not passed to grading.
