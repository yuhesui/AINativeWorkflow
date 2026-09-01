# AI-Native Workflow v5.6.36 — Enhanced Development Package

AI-Native Workflow is a repository-centred operating model for long-horizon AI-assisted work. It separates durable intent, planning, machine execution, evidence, verification, and human authority.

## Operational boundary

Only the following directory is the operative runtime passed to a Main chat or installed into a target repository for a coding-agent Orchestrator:

```text
.ai-workflow/
```

Everything else in this archive is development, research, publication, submission, or teaching-material storage about AI-Native Workflow itself. Those outer materials are not automatically loaded into project agents.

## Recommended realization

```text
Human
  ↓
Main chat
  ├─ optional Research → Main reconciliation
  ├─ optional Theory
  └─ optional Experiment
  ↓
whole-Phase plan: one DIC package
  ├─ DIC/README.md
  ├─ DIC/REQUESTS.md
  └─ DIC/PLAN.md
       └─ durable sequence, dependencies, parallelism, merge and repair branches
  ↓
coding-agent Orchestrator
  ↓
JIT EPS attempts → model-tuned prompts → bounded Workers/subagents → evidence
  ↓
Verifier / Main reconciliation
```

Main is a persistent user-facing planning and decision chat. Orchestrator is a repository-aware coding-agent session such as Codex or Claude Code. Main does not operate as a terminal-heavy execution dashboard; the Orchestrator does not redefine user intent or material science.

## What is new in v5.6.36

- a concise Main starter and whole-Phase checklist;
- explicit separation between the Core scientific workstreams and the Core DIC views;
- explicit `Main → Research → Main reconciliation → Phase/DIC` decision-support path;
- one DIC package per Phase, with the durable prompt/dependency graph kept in `DIC/PLAN.md`;
- stronger Orchestrator rules for bounded prompt decomposition, subagents, parallelism, write ownership, and integration;
- mandatory model/surface tuning of every concrete EPS prompt using current official-provider-derived guidance;
- current OpenAI and Anthropic prompting source lock and distilled guides;
- a complete Who Verifies the Agents? submission directory and anonymous runnable supplement;
- a new `slides/` section with a NeurIPS 2026 Education Track slide plan and teaching-material plan.

## Start here

- Human or Main: `.ai-workflow/docs/MAIN.md`
- Coding-agent Orchestrator: `.ai-workflow/docs/ORCHESTRATOR.md`
- Prompt generation: `.ai-workflow/docs/PROMPTING_CORE.md`
- Research: `.ai-workflow/docs/RESEARCH.md`
- Ready-to-copy runtime ZIP: `runtime_release/AI_WORKFLOW_RUNTIME_v5.6.36.zip`
- Package map: `PACKAGE_CONTENTS.md`
- Who Verifies submission: `submissions/who_verifies/`
- Education Track preparation: `slides/NEURIPS_2026_EDUCATION_SLIDE_PLAN.md`

## Validation

Run from this directory:

```bash
python .ai-workflow/aw.py validate
python .ai-workflow/aw.py demo --output demo_trace.json
python -m unittest discover -s .ai-workflow/tests -v
```

No external submission or public release is performed by this package.
