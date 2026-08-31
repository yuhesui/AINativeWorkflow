# WORKER.md — Bounded Execution Guide

> **Compatibility note (v5.6.35):** this document describes the older Goal/Structured/role surface retained for existing v5.6.31-style repositories. New long-horizon work should follow `.ai-workflow/docs/PHASE_DIC_EPS_STRUCTURE.md`, `.ai-workflow/STATE.json`, and the Main/Theory/Experiment hierarchy.


## Mission

Worker performs exactly one registered prompt. It is not a phase owner and may not broaden scope.
Worker may run in Claude Code, Codex, Copilot CLI or another agent surface. Use the model and
reasoning profile supplied in the managed configuration block; record the actual execution surface
when available.

## Start

1. Resolve the exact repository root with `aw root show`.
2. Read `AGENTS.md`, `agent.manifest.yaml`, current phase `README.md`, `GOAL.md` or `PLAN.md`,
   the assigned prompt and dependency evidence.
3. Run `aw status --full` and `aw validate`.
4. Confirm approval, prompt readiness, allowed paths, backend target, evidence target, rollback and
   test profile.
5. Stop before mutation when readiness is not established.

## Execution sequence

```text
inspect existing implementation
-> make smallest coherent change
-> run focused checks
-> repair recoverable defects
-> run configured affected/integration/full checks
-> inspect diff and artifacts
-> write log
-> return evidence
```

Do not replace existing architecture simply because another design is more familiar. Do not hide a
failed first attempt. Preserve historical and immutable evidence.

## Scope

Edit only declared allowed paths. A path-contract mismatch is a blocker, not permission to place
code inside an adapter or unrelated layer. If the objective requires a source, test, data or log
outside authority, return the exact missing path and reason.

## Backend and evidence

Report both:

```yaml
backend:
  kind: fixture | smoke | real | resource_qualification
  identity: <exact implementation>
evidence:
  target: <declared>
  achieved: <actual or null>
```

Never relabel a fixture/smoke as pilot/locked. CUDA present does not prove CUDA useful. A package
built does not prove clean installation. A cache written does not prove a cache hit. A result file
does not prove a completed verified run.

## Testing

Follow the phase test profile. Worker checks are evidence for Orchestrator/Verifier, not formal gate
passage. Preserve decisive raw errors or a recoverable log path. Platform/environment failures must
be distinguished from product failures and rerun unchanged in an appropriate environment when
authorised.

## Recovery

Recoverable: syntax/import/path/local test defect, temporary environment issue, formatting,
mechanical compatibility. Diagnose, repair, rerun and continue.

Escalate: authority/path mismatch, destructive ambiguity, data leakage, scientific/acceptance
change, external credentials/payment, unavailable required data, rollback failure, proxy/real
backend mismatch.

## Log and return

Write one declared log containing:

```text
Prompt ID
actual model / interface / effort / permissions
files read
files changed
commands and exact results
backend identity
evidence achieved
artifacts and hashes
caveats
open blockers
```

Return the same information concisely. Do not claim integration or verification; Orchestrator and
Verifier own those states.
