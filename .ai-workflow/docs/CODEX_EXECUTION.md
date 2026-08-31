# CODEX_EXECUTION.md — Codex CLI Operating Pattern

Codex CLI normally hosts Orchestrator or Worker. Main remains a persistent GPT-5.6 Pro chat when
available.

## Start

- run from the configured repository root;
- read `AGENTS.md`, phase README and assigned prompt;
- inspect permission mode before mutation;
- use one prompt at a time;
- preserve exact commands, diffs and raw decisive failures.

## Modes

Use the narrowest mode that can perform the task. A prompt granting source edits does not grant
external network, release, destructive cleanup or credentials. Full-auto style operation is
appropriate only when the phase and prompt explicitly authorize it and rollback is adequate.

## Orchestrator

Use `aw next --print` or the prompt file, inspect current state, generate bounded repair prompts,
and update lifecycle with evidence. Do not turn the Codex session into Main by making material
user-intent decisions without escalation.

## Worker

Implement only allowed paths; run risk-adaptive tests; preserve failed attempts and report backend
and evidence accurately.

## Reset and handoff

All state must be reconstructable from repository files. After context reset, run `aw status --full`
and read the current prompt/evidence before continuing.
