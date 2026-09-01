# PROMPTING_CORE.md — Normative Prompt-Compilation Rules

These rules are distilled from current official OpenAI and Anthropic guidance. Provider documents are source guidance; the DIC remains the task authority.

## 1. Start from the outcome

Every prompt begins with one primary outcome and observable success criteria. State the required deliverable and evidence. Do not lead with a long invented procedure unless the procedure itself is contractual.

## 2. Include only decision-relevant context

Provide:

- exact repository/Phase/DIC/EPS identity;
- current state and dependencies;
- relevant files and evidence;
- hard constraints and non-goals;
- authority and approval boundaries;
- required output and validation.

Do not load the entire development distribution or every historical report into a Worker context. Only `.ai-workflow/` is the stable runtime; task-local evidence is loaded on demand.

## 3. State each instruction once

Avoid repeated warnings, duplicated role prose, and several versions of the same approval rule. Preserve repetition only where a self-contained coding-agent prompt genuinely needs a path, output, or stop rule that otherwise would be hidden.

## 4. Define autonomy once

Name safe local actions that may proceed without interruption. Separately name actions requiring confirmation: external writes, destructive mutation, purchases/paid compute, credentials/private systems, public release/submission, and material scope expansion.

## 5. Specify output and evidence

State:

- exact output paths and schemas;
- evidence class and ceiling;
- checks and commands where known;
- failure representation;
- retry and stopping limits;
- what must be returned to the parent.

A result is incomplete when it omits required evidence even if the implementation appears plausible.

## 6. Leave non-contractual execution choices to the model

Allow the executor to choose local implementation details and tool order when those choices do not affect the DIC, safety, evidence, or reproducibility. Do not prescribe hidden reasoning or demand visible chain-of-thought.

## 7. Compile against the actual model and surface

Before dispatch, Orchestrator resolves the selected model/surface and applies the relevant overlay:

```text
OpenAI / GPT-5.6 / Codex → GPT56_ROUTING.md + CODEX_EXECUTION.md
Anthropic / Claude Code   → CLAUDE_EXECUTION.md
```

Then remove duplicates and re-check the complete prompt. A generic template is never the final prompt merely because all placeholders are filled.

## 8. Prefer bounded prompts

One prompt normally has one primary outcome and one to three tightly coupled work packages. Split when tasks have different dependencies, expertise, evidence types, write owners, parallelism, or failure semantics. Do not split into one prompt per shell command.

## 9. Use examples selectively

Use examples when they encode a required schema, style, edge case, or measured correction. Do not let an example silently become the architecture or an exhaustive solution.

## 10. Structure complex prompts

Use clear headings or tags to separate:

```text
role
outcome and acceptance
current state and dependencies
read first
allowed/forbidden scope
work
outputs
checks/evidence
repair/stop
return
```

For Claude, XML-style sections may improve separation. For all models, put the most load-bearing task instructions where they are easy to locate and avoid burying the query after irrelevant context.

## 11. Tool and subagent orchestration

- expose only relevant tools;
- describe input/output/error semantics precisely;
- batch independent read-only calls when safe;
- keep ordered or side-effecting calls sequential;
- use subagents for independent parallel work, isolated context, or specialization;
- work directly for simple, sequential, single-file, or shared-state tasks;
- declare one parent integration point.

## 12. Prompt audit before dispatch

Confirm:

- one primary outcome;
- request/plan-node mapping;
- current dependencies/evidence;
- correct model/surface overlay;
- no material duplication;
- all outputs fit allowed paths;
- checks match the claimed evidence class;
- subagent/parallel choices are justified;
- stop/escalation rules are explicit;
- return contract is complete.
