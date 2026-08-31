# NEXT_PHASE.md — Next-Phase Generation Guide

## Trigger

Generate a new phase only from a verified handoff or a clearly recorded current-state audit. Do not
continue a completed phase by silently reopening locked contracts.

## Inputs

- previous `FINAL_HANDOFF.md` and verification;
- current branch/revision/status;
- remaining requests and deferred items;
- new rough user input;
- authority and release state;
- model/compute/tool availability;
- lessons from blocked/failed prompts.

## Decision

Classify the next work as:

```text
continuation
deferred completion
versioned scientific amendment
release/submission phase
new independent objective
```

Choose Goal Mode when one outcome dominates and route discovery should adapt. Choose Structured
Mode when architecture, experiments, migration, release or multiple coupled packages must be
frozen in advance.

## CLI

```bash
aw phase plan-next phase_02_name \
  --mode structured \
  --execution-level high \
  --research-level mid \
  --test-profile integration \
  --from-handoff phases/phase_01/reports/FINAL_HANDOFF.md \
  --rough-input "..."
```

Review the generated proposal, then add `--create`. After any config/root/model change run:

```bash
aw update --all-phases
aw validate --phase phase_02_name
```

By default, `aw update` does not rewrite terminal prompts. The new phase receives current config at
creation.

## Structured requirements

Main must write complete requests, plan, approval, architecture/contract, prompt pack, verifier
and handoff prompts. Copy full templates and replace placeholders with project-specific content.

## Goal requirements

Main writes one complete `GOAL.md`; Orchestrator generates the plan/prompts after GO. Acceptance
must be explicit before approval.

## Anti-patterns

- copy old prompts without reconciling current code;
- treat deferred release as authorised;
- carry old seeds into a “fresh” locked experiment;
- rename a failed phase as complete;
- create excessive documents with no decision value;
- ask the user to allocate Workers manually when Orchestrator can route them.
