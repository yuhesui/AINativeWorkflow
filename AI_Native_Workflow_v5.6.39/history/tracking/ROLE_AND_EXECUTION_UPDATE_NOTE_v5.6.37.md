# Technical-Report Update Note — Main, DIC Planning, and Coding-Agent Orchestration

## Normative practical realization

The long-form report should distinguish the abstract role model from the recommended operational surfaces:

| Function | Recommended realization |
|---|---|
| Main | persistent user-facing chat for interpretation, Plan/Phase decisions, one-DIC planning, material adjudication, and closure |
| Theory | optional specialist chat/reasoning workstream |
| Experiment | optional specialist chat/reasoning workstream |
| Research | optional advisory evidence pass returning to Main for reconciliation |
| Orchestrator | repository-aware coding-agent session such as Codex or Claude Code |
| Worker/subagent | bounded child of the coding-agent Orchestrator |
| Verifier | independent gate where consequence/evidence warrants it |

## One DIC per Phase

Each Phase has exactly one multi-view durable intent contract:

```text
DIC/README.md
DIC/REQUESTS.md
DIC/PLAN.md
```

`PLAN.md` contains the durable prompt/dependency graph, including sequence, parallel subagents, merge nodes, evidence gates, and conditional repair/review branches. This graph is planned by Main at whole-Phase level.

The coding-agent Orchestrator realizes ready DIC plan nodes as one or more disposable EPS attempts. It owns the actual prompt instances, executor routing, bounded subagents, integration, repair, and verification dispatch.

## Research path

The report should make this visible without turning Research into mandatory overhead:

```text
Main question
→ optional Research
→ Main reconciliation / binding decision
→ one Phase DIC
→ coding-agent Orchestrator
```

A Research result is advisory evidence, not a DIC amendment or implementation result by itself.

## Prompting and subagents

The report should state that:

- generic templates are scaffolds rather than final prompts;
- the coding-agent Orchestrator tunes each EPS prompt to the actual selected model/surface using current official-provider-derived guidance;
- one prompt normally has one primary outcome and one to three tightly coupled work packages;
- prompt boundaries should follow dependencies, expertise, evidence class, write ownership, parallelism, and failure semantics;
- subagents are actively considered for genuinely independent/isolated/specialized work, with disjoint writes and one explicit parent integration point;
- Worker completion is not Orchestrator integration, and integration is not Verifier acceptance.

## Runtime boundary

Only `.ai-workflow/` is installed in or handed to target projects. The full report, research, workshop submissions, slides, and historical artifacts remain outer development/reference storage.


## Human-attention objective (v5.6.38)

The long-form report now uses **human attention required per unit of verified research progress** as the practical optimization target rather than generic “save time” language. It defines benchmark-relative human-attention intensity, treats DIC as a human-intelligibility projection, and adds attention/reconstruction events to the controlled evaluation programme. This is an empirical target, not an already-established gain.

The report also distinguishes `Primary Aim` from constraints/supporting/optional branches to make two semantic drifts visible: constraint–objective inversion (defensive drift) and salience flattening.
