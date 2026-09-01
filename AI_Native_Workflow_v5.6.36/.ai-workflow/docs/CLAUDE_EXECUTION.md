# CLAUDE_EXECUTION.md — Claude / Claude Code Overlay

## Clear and structured instructions

- State the outcome, context, constraints, and output directly.
- Use headings or XML-style sections when they clarify mixed instructions, examples, documents, and required outputs.
- Explain the reason for unusual constraints when it improves correct generalization.
- Use examples only where format or behavior is materially ambiguous.

## Parallel tool use

Claude can issue independent tool calls in parallel. Encourage parallelism only for calls that do not depend on one another and do not mutate shared state. Execute ordered, side-effecting, or shared-state calls sequentially. Never guess missing parameters to fill a parallel batch.

## Subagent orchestration

Use subagents when tasks:

- can run in parallel;
- benefit from isolated context;
- form independent workstreams;
- require specialized investigation, review, verification, or repository-region analysis.

Work directly for simple tasks, sequential operations, single-file edits, or steps that require continuous shared context. Guard against over-delegation when a direct search/read is faster and sufficient.

Every subagent receives a bounded outcome, read/write scope, evidence requirement, stop rule, and parent return schema. Parent Orchestrator remains responsible for integration.

## Claude Code practice

- use project instructions and explicit permissions;
- inspect files before claims or edits;
- use separate worktrees/sandboxes for parallel coding branches where appropriate;
- prefer writer/reviewer or implementation/verification separation for consequential changes;
- retain a durable task list/state for long-running work;
- clean temporary scratch files before completion;
- validate the integrated repository, not only isolated child branches.

## Prompt tuning

Adapt every EPS prompt to the actual Claude/Claude Code model and available tools. Templates are scaffolds. Remove duplicate instructions and avoid aggressive repeated wording that can cause over-triggering of tools or subagents.

## Source lock

See `OFFICIAL_PROMPTING_SOURCES.md`. Refreshed 2026-09-01 from official Anthropic documentation.
