# CORE.md — AI Native Workflow Operating Model

## Runtime boundary

Only `.ai-workflow/` is the operative package supplied to Main and coding-agent execution surfaces. Technical reports, workshop submissions, research archives, and slides in the surrounding development distribution are not runtime instructions unless a Phase explicitly imports them.

## Two distinct role layers

### Core scientific workstreams

```text
Main | Theory | Experiment
```

- **Main** is always present and owns interpretation, programme/Phase planning, authority, integration of specialist advice, material decisions, and closure.
- **Theory** is activated when formal reasoning, literature/novelty, counterexamples, or conceptual interpretation materially matter.
- **Experiment** is activated when methodology, benchmark design, frozen protocols, statistical analysis, or experimental interpretation materially matter.

Theory and Experiment are standard specialist chat/reasoning workstreams, not mandatory participants in every Phase.

### Machine execution

```text
coding-agent Orchestrator → bounded Workers/subagents → tools/actions
```

Orchestrator is a repository-aware coding-agent session such as Codex or Claude Code. Main authors the approved Phase DIC **and the initial EPS/prompt graph**. Orchestrator validates that package, compiles each prompt for the actual model/surface, schedules and executes it, integrates evidence, and may create a bounded superseding repair EPS under the same DIC when execution-local defects occur.

## Research is an optional decision-support layer

```text
Main → Research → Main reconciliation → Phase/DIC → Orchestrator
```

Research is used only when external sources can materially change a method, architecture, experiment, implementation choice, claim, venue, or release decision. Research does not gain mutation authority and is not implementation or experiment evidence. Main must reconcile Research before it becomes binding.

## Hierarchy

```text
Goal → Plan → Phase → DIC → EPS → Prompt/Run → Action
```

- **Goal / Plan:** stable programme authority.
- **Phase:** one coherent machine-managed milestone.
- **DIC:** exactly one durable multi-view contract for the Phase.
- **EPS:** a disposable executable realization of DIC plan nodes for one attempt. The initial EPS is authored by Main; bounded repair EPS revisions may be created by Orchestrator under the unchanged DIC.
- **Prompt/Run:** one bounded executor invocation.
- **Action:** a primitive tool call, edit, test, search, or experiment operation.

## Core DIC views

Every Phase DIC has exactly these required views:

```text
DIC/README.md
DIC/REQUESTS.md
DIC/PLAN.md
```

`DIC/PLAN.md` stores the durable prompt/dependency graph, including sequence, dependencies, parallel subagents, merge nodes, evidence gates, and conditional review/repair branches. Optional views such as `ARCHITECTURE.md` or `TEST_MATRIX.md` are added only when useful.


## Default Phase filesystem

Project-specific state belongs at repository root:

```text
phases/<phase_id>/
├── DIC/
├── EPS/
├── ORCHESTRATOR_START.md
├── reports/
├── results/
├── evidence/
├── artifacts/
└── logs/
```

`reports/PHASE_SUMMARY.md` is the compact human-facing state. `reports/FINAL_HANDOFF.md` is required at terminal handoff. Preserve `results/KEY_RESULTS.json` when key findings are naturally structured and `KEY_RESULTS.csv` when tabular form is natural. `evidence/EVIDENCE_MANIFEST.json` indexes decisive evidence; raw logs and generated artifacts remain separate.

## Human-attention objective

The workflow optimizes neither raw human time nor model-call count as a universal objective. Its practical target is to reduce **human attention required per unit of verified research progress** while preserving scientific quality, authority, and evidence. Routine coordination, state reconstruction, prompt routing, and local repair should move toward machine-managed surfaces; human attention should concentrate on the objective, surprising evidence, material methodological choices, claim boundaries, and external responsibility.

This is a design and evaluation objective, not an already-established empirical performance claim. Long or heavily verified runs may use more total inference or wall-clock time.

The DIC therefore has two jobs: it is a durable semantic contract **and** a human-intelligibility interface. As machine execution becomes more complex, the human-facing state should become more compact and decision-relevant rather than forcing the researcher to reconstruct raw prompt trees, logs, and failed branches.

## Principal control rule

Main plans and authorizes the whole Phase, authors the DIC, and materializes the **initial EPS/prompt graph**. Orchestrator executes the whole Phase by validating that EPS, model-tuning its concrete prompts, scheduling Workers/subagents, integrating evidence, and issuing bounded repair EPS revisions when necessary. Ordinary execution failure normally changes EPS, not the DIC.
