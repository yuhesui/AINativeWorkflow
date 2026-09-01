# CORE.md — AI-Native Workflow Operating Model

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

Orchestrator is a repository-aware coding-agent session such as Codex or Claude Code. It realizes the approved Phase/DIC as JIT EPS attempts, concrete prompts/runs, tool use, integration, bounded repair, and verification dispatch.

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
- **EPS:** a disposable JIT operational realization of DIC plan nodes for one attempt.
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

## Principal control rule

Main plans and authorizes the whole Phase at DIC level. Orchestrator executes the whole Phase by producing model-tuned EPS prompts and managing bounded Workers/subagents. Ordinary execution failure normally changes EPS, not the DIC.
