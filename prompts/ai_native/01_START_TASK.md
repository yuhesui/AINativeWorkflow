Treat the task I now provide as the approved Goal. This is the single Main inference for the currently revealed scope. Use the loaded AI-Native Workflow autonomously and return the actual complete, importable execution package—not a prose plan, outline, sample, partial scaffold, or one-prompt summary. Create the Plan and Phase decomposition you judge appropriate. Fully materialize the complete current active Phase, including its complete DIC and complete initial EPS prompt graph, before returning the package. Use evidence-gated accept/repair/replan/escalate semantics, retain failures and negative evidence, and keep durable repository state sufficient for a fresh Main to recover. Do not force a predetermined number of Phases and never cross an unrevealed-checkpoint gate.

Return exactly one self-contained whole-Phase ZIP attachment named `MAIN_HANDOFF.zip` (an alternate downloaded ZIP filename is acceptable). Do not tell the operator to create a path or claim that you saved anything into their local repository; the operator will download and import the archive. Include every canonical file needed to execute the entire currently revealed Phase: the complete Plan/Phase state; `PHASE_MANIFEST.json`; all required DIC views including the full dependency graph; the complete initial EPS manifest; a distinct, substantive prompt file for every EPS node; `ORCHESTRATOR_START.md`; and all changed durable workflow state/index files needed to import and recover that state. Do not collapse multiple independently verifiable EPS nodes into one omnibus prompt merely to produce fewer files.

The importer contract is strict. The ZIP must have exactly this shape, either at archive root or beneath one optional enclosing directory:

```text
[optional-wrapper/]
  HANDOFF_MANIFEST.json
  <repository_overlay>/
    .ai-workflow/
      .ai-workflow/
        ... changed durable runtime state/index files ...
      phases/<phase_id>/
        PHASE_MANIFEST.json
        DIC/README.md
        DIC/REQUESTS.md
        DIC/PLAN.md
        EPS/<eps_id>/manifest.json
        EPS/<eps_id>/prompts/<node_id>.md
        ORCHESTRATOR_START.md
```

`HANDOFF_MANIFEST.json` must be a JSON object. It must record the exact operator-supplied `task_id`, `run_id`, and `task_lock_sha256`, plus the safe handoff ID, condition `AI_NATIVE`, selected executor, requested model and effort, `repository_overlay`, package-relative `executor_prompt`, Plan/Phase/DIC/EPS/prompt lineage, allowed paths/actions, expected tests/evidence, and `archived_files`. Copy the three binding values exactly; never infer or reuse them from another task. `archived_files` must contain the exact package-relative path of every file below the optional wrapper, including `HANDOFF_MANIFEST.json`; do not prefix paths with the optional wrapper name. No declared file may be absent and no file may be undeclared. Every non-manifest file must be beneath the declared overlay. That overlay may contain only the canonical root `.ai-workflow/` state and root `phases/` Phase state. Set `executor_prompt` to the package-relative `ORCHESTRATOR_START.md`, not to one EPS worker prompt, so the CLI orchestrator executes the complete EPS graph. Do not add sibling entries beside the optional wrapper or use more than one enclosing directory.

Every EPS node must have its own directly runnable prompt file stating its bounded outcome, live context, dependencies, authority boundaries, acceptance criteria, verification, evidence to preserve, and exact return contract. Tailor every prompt to the selected Codex CLI or Claude Code CLI model using the frozen route supplied by the operator. The EPS manifest must enumerate the full node graph and point unambiguously to every prompt file. Do not package unrelated completed Phases, task-code changes, or private evaluator material.

The ZIP is a transport copy of canonical durable state, not a competing workflow surface. The operator imports its workflow overlay into the surviving scored repository before execution. If the package is rejected before import, correct the package and return a replacement for the same unexecuted handoff. After any successful import or executor attempt, do not replay the same package: integrate returned evidence into the same canonical Phase and create a new handoff ID and new EPS instance for an ordinary retry unless the actual Phase objective or contract changed materially.
