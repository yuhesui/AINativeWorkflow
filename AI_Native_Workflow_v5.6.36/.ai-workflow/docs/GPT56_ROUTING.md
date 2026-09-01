# GPT56_ROUTING.md — OpenAI Model and Prompting Overlay

## Purpose

Use this overlay for GPT-5.6-family and ChatGPT/Codex work. Actual model/surface availability must be checked rather than inferred from a subscription label.

## Prompting characteristics

- Prefer lean, outcome-focused prompts.
- State each instruction once.
- Provide domain context, hard constraints, approval boundaries, evidence, success criteria, and output format.
- Do not prescribe every step when the execution path is not part of the contract.
- Do not ask for visible chain-of-thought.
- Define which tools may be used, exact output schema, required evidence, concurrency, retry, and stopping limits for tool-heavy work.
- Count lower tokens/calls/latency as an improvement only when the final result still passes the quality and evidence gate.

## Routing intent

- Main and material scientific decisions: strongest available persistent chat/reasoning configuration.
- Complex coding Orchestrator: strongest available Codex/GPT-5.6 route justified by ambiguity and consequence.
- Bounded implementation: balanced route where measured quality is sufficient.
- Mechanical/deterministic work: economical route plus deterministic validation.
- Formal acceptance: fresh high-capability context where practical.

## Multi-agent/subagents

Use multiple agents when the Phase decomposes cleanly into independent workstreams and the parent can synthesize explicit returns. Avoid parallelizing tightly shared state or substituting several weak contexts for one coherent difficult decision.

## Source lock

See `OFFICIAL_PROMPTING_SOURCES.md`. Refreshed 2026-09-01 from official OpenAI documentation.
