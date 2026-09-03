# Migration and Legacy Terminology

Current default architecture: `Goal -> Plan -> Phase -> DIC -> EPS -> Prompt/Run -> Action`.

Current scientific workstreams: `Main | Theory | Experiment`; Research is a capability.

Current execution: coding-agent Orchestrator -> bounded Workers/subagents.

Each Phase has exactly one multi-view DIC with Core `README.md`, `REQUESTS.md`, `PLAN.md`. `PLAN.md` owns the durable sequence/dependency/parallelism graph; EPS is disposable.

Older Goal/Structured/Minor-centric documentation is historical and should not override current package state. Small non-research maintenance may still use bounded execution, but it is not a primary concept in the research-facing architecture.
