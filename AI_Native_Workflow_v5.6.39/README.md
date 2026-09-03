# AI Native Workflow 5.6.39

AI Native Workflow is a repository-backed operating framework for long-horizon AI-assisted research and other multi-artifact technical work. It formalizes the informal workflows researchers increasingly build from persistent chat, research tools, and coding agents so that current AI systems can take on more coordination/execution without requiring proportionally more human supervisory attention.

## What to copy into a project

Copy **only** the complete `.ai-workflow/` directory into the target repository root.

The rest of this archive is development storage for AI Native Workflow itself: technical report, research/theory, experiments, submissions, slides, validation, and history.

## Current architecture

```text
Goal -> Plan -> Phase -> DIC -> EPS -> Prompt/Run -> Action
```

Core scientific workstreams:

```text
Main | Theory | Experiment
```

Research is an optional decision-support capability. Main authors the approved whole-Phase DIC **and the initial EPS/prompt graph**. The coding-agent Orchestrator validates and model-tunes that EPS for the actual execution surface, runs bounded Workers/subagents, integrates evidence, and may issue bounded repair EPS revisions under the unchanged DIC.

Each Phase has exactly one DIC with Core views:

```text
README.md | REQUESTS.md | PLAN.md
```

`PLAN.md` contains the durable sequence/dependency/parallelism graph. Project-specific Phase state lives at root `phases/<phase_id>/`, while `.ai-workflow/` remains the reusable runtime.

## Human-attention objective

The workflow does not promise universally lower wall-clock time, tokens, or inference cost. Its practical objective is lower **human attention required per unit of verified research progress**, while preserving scientific quality, evidence, and authority.

## Read order

1. `00_READ_FIRST.md`
2. `CURRENT_STATE.md`
3. `QUICKSTART.md`
4. `technical_report/AI_NATIVE_WORKFLOW_TECHNICAL_REPORT.pdf` for the detailed scientific rationale
5. `.ai-workflow/guides/DETAILED_WORKFLOW_GUIDE.md` for full operating/maintenance detail

## Tracking

- `CURRENT_STATE.md` — what is true now
- `ROADMAP.md` — future work
- `CHANGELOG.md` — history
- `PACKAGE_MANIFEST.json` — file inventory/hashes
- `PACKAGE_HANDOFF.json` — machine-readable recovery state

Superseded tracking material is under `history/`.
