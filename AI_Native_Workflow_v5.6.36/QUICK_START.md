# Quick Start

## 1. Install the runtime

Copy the entire directory below into the root of the target repository:

```text
.ai-workflow/
```

Do not copy individual runtime files selectively. The surrounding folders in this development archive are references and submission assets, not the installed runtime.

## 2. Start Main

Give the Main chat access to the target repository and instruct it to read:

```text
.ai-workflow/docs/CORE.md
.ai-workflow/docs/MAIN.md
```

Main should recover the repository state, interpret the objective, decide whether decision-relevant Research/Theory/Experiment work is needed, and plan the next whole Phase as exactly one multi-view DIC package.

## 3. Review the whole-Phase DIC

The Core DIC views are:

```text
DIC/README.md
DIC/REQUESTS.md
DIC/PLAN.md
```

`PLAN.md` is where Main records the durable sequence, dependencies, parallel branches, merge points, conditional repair/review branches, evidence targets, and stop boundaries. It is not the current EPS attempt.

## 4. Execute with a coding-agent Orchestrator

Give the approved Phase/DIC and `.ai-workflow/` to Codex, Claude Code, or another repository-aware coding agent. The Orchestrator:

- validates readiness;
- realizes DIC plan nodes as one or more JIT EPS attempts;
- tunes each concrete execution prompt to its selected model/surface;
- separates broad work into bounded prompts;
- uses subagents when work is independent, parallel, or benefits from isolated context;
- integrates evidence and invokes verification;
- regenerates EPS after ordinary repair without silently changing the DIC.

## 5. Review evidence at the Phase boundary

Main receives compact evidence and a verifier result, then closes, repairs, replans, or escalates the whole Phase. Main should not be fed every terminal event or internal Worker transcript.
