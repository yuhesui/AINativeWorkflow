# AI Native Workflow — Current State

**Version:** 5.6.39  
**Date:** 3 September 2026

## Primary Aim

Maintain a reusable, research-grade AI workflow that lets current persistent-chat, research, and coding-agent systems perform substantially more long-horizon work while keeping scientific intent, evidence, execution state, and consequential authority inspectable and recoverable.

The principal operational objective is **lower human attention required per unit of verified research progress**, subject to scientific quality, evidence, and authority constraints. This remains an evaluation target, not an established comparative result.

## Current Architecture

Canonical hierarchy:

```text
Goal -> Plan -> Phase -> DIC -> EPS -> Prompt/Run -> Action
```

Core scientific workstreams:

```text
Main | Theory | Experiment
```

- Main is the persistent user-facing planning and decision chat.
- Theory and Experiment are optional specialist reasoning workstreams.
- Research is a cross-cutting decision-support capability returning to Main for reconciliation.
- The Orchestrator is a repository-aware coding-agent surface such as Codex or Claude Code.
- Workers/subagents perform bounded execution.
- Verifier returns `accept`, `repair`, `replan`, or `escalate`.

Every Phase has exactly one multi-view DIC with Core views:

```text
DIC/README.md
DIC/REQUESTS.md
DIC/PLAN.md
```

`PLAN.md` owns the durable sequence/dependency/parallelism graph. Main materializes that graph into the **initial EPS/prompt graph** for the Phase handoff. The coding-agent Orchestrator validates and model-tunes that EPS for the actual execution surface; ordinary execution failure normally creates a bounded superseding repair EPS rather than rewriting the DIC.

## Human-Attention / Salience Framing

The DIC is both a machine contract and a human-intelligibility interface. As machine execution grows, the human-facing state should become more compact and decision-relevant rather than forcing the researcher to reconstruct raw prompt trees and logs.

Two explicit semantic failure patterns are tracked:

- **constraint-objective inversion / defensive drift** — constraints such as defensibility replace the Primary Aim;
- **salience flattening** — many locally reasonable branches receive similar weight until the research loses a central contribution.

Main preserves one explicit Primary Aim and separates supporting questions, constraints, optional branches, non-goals, and deferred work.

## Runtime Status

The operative runtime lives only under `.ai-workflow/`. Compact normative docs remain under `.ai-workflow/docs/`; a restored detailed human/maintainer reference layer now lives under `.ai-workflow/guides/`.

Runtime schema/package version: **5.6.39**.

Current validation status is recorded in `validation/CURRENT_VALIDATION.md`.

## Technical Report

The canonical detailed report is now restored to long-form depth:

```text
technical_report/AI_NATIVE_WORKFLOW_TECHNICAL_REPORT.tex
technical_report/AI_NATIVE_WORKFLOW_TECHNICAL_REPORT.pdf
```

It is approximately 58 pages and combines:

- detailed literature and modern model/agent-surface background;
- current architecture and design rationale;
- human-attention and Primary Aim/salience framing;
- formal refinement / verification / dependency-locality theory;
- reference implementation semantics;
- detailed operational protocols;
- matched-budget evaluation and attention measurement design;
- appendices with DIC, executor, verifier, attention-record, and tracking-file examples.

## Detailed Guide

`.ai-workflow/guides/DETAILED_WORKFLOW_GUIDE.md` is the complete operating/maintainer guide. It is intentionally detailed and is not a default Worker prompt.

## Research / Theory State

The package retains the current claim ledger, theory note, literature matrix, novelty synthesis, and primary-source scan under `research/`. Formal dependency-local recovery and related structural results remain conditional on explicit assumptions; no theorem novelty is claimed merely because the workflow integrates those ideas.

## Experiment State

The matched-budget long-horizon / recovery evaluation remains planned rather than confirmatory. Current deterministic fixtures establish runtime/structural behavior only. Human-attention intensity has not yet been empirically validated.

## Submission State

### Managing Agents that Manage Agents — NeurIPS 2026

Track decision: **Full Paper**. The current draft is under `submissions/meta_agents/`. It frames AI Native Workflow as a meta-agent management protocol and treats human-attention efficiency as a target rather than a proven gain.

### Who Verifies the Agents? — NeurIPS 2026 Workshop

Demo-paper package is retained under `submissions/who_verifies/`, including the anonymous runnable supplement and OpenReview metadata.

### NeurIPS 2026 Education Track

Preparation material is under `slides/` and `submissions/neurips_education/`. The concept is **AI Native Workflow for Research**: a formalized/adaptable version of the multi-surface AI workflows researchers already use, with hierarchical planning as an enabling mechanism rather than the entire topic.

### AutoMLR

Existing eligibility material is retained; no qualifying distinct autonomous ML result is asserted merely from workflow/system evidence.

## Known Limitations

- no confirmatory matched-budget agent comparison yet;
- no confirmed human-attention reduction yet;
- dependency-local repair assumes sufficiently complete dependency declarations;
- verifier correctness is limited by its evidence surface;
- DICs can shift rather than reduce burden if they are verbose or poorly prioritized;
- provider/model guidance is time-sensitive;
- hierarchy can be unnecessary overhead for small tasks.

## Canonical Tracking Rule

`CURRENT_STATE.md` states what is true now.  
`ROADMAP.md` states what happens next.  
`CHANGELOG.md` records what changed historically.  
Superseded status reports remain under `history/` and do not compete with current state.


## v5.6.39 minor clarification

- **Initial EPS ownership:** Main authors the initial EPS/prompt graph together with the Phase DIC. Orchestrator validates and model-tunes prompts for the actual execution surface; bounded execution defects may create repair EPS revisions under the same DIC.
- **Phase filesystem:** root `phases/<phase_id>/` is the default project-local analysis surface, with DIC, EPS, reports, results, evidence, artifacts, and logs.
- **Phase ZIP import:** `aw phase import <zip>` safely imports and registers a Main-authored Phase package.
