Treat the task I now provide as the approved Goal. Use the loaded AI-Native Workflow autonomously. Create the Plan you judge appropriate; for each active Phase, materialize its canonical Phase folder with the required DIC views and a just-in-time EPS before bounded execution. Use evidence-gated accept/repair/replan/escalate semantics, retain failures and negative evidence, and keep durable repository state sufficient for a fresh Main to recover. Do not force a predetermined number of Phases.

For every bounded CLI-executor handoff on the current task, return one self-contained Phase ZIP attachment named `MAIN_HANDOFF.zip` (an alternate downloaded ZIP filename is acceptable). Do not tell the operator to create a path or claim that you saved anything into their local repository; the operator will download and import the archive. Include the complete current Phase DIC, assigned EPS, exact executor prompt, all changed durable workflow-index/Plan/Phase files needed to import that state, and a package-root `HANDOFF_MANIFEST.json`.

The importer contract is strict. The ZIP must have exactly this shape, either at archive root or beneath one optional enclosing directory:

```text
[optional-wrapper/]
  HANDOFF_MANIFEST.json
  <repository_overlay>/
    .ai-workflow/
      ... importable Plan/Phase/DIC/EPS/prompt files ...
```

`HANDOFF_MANIFEST.json` must be a JSON object. It must record the exact operator-supplied `task_id`, `run_id`, and `task_lock_sha256`, plus the safe handoff ID, condition `AI_NATIVE`, selected executor, requested model and effort, `repository_overlay`, package-relative `executor_prompt`, Plan/Phase/DIC/EPS/prompt lineage, allowed paths/actions, expected tests/evidence, and `archived_files`. Copy the three binding values exactly; never infer or reuse them from another task. `archived_files` must contain the exact package-relative path of every file below the optional wrapper, including `HANDOFF_MANIFEST.json`; do not prefix paths with the optional wrapper name. No declared file may be absent and no file may be undeclared. Files may use subfolders, but every non-manifest file must be beneath the declared overlay and that overlay may contain only a root `.ai-workflow/` subtree. The executor prompt itself must be inside that overlay. Do not add sibling entries beside the optional wrapper or use more than one enclosing directory.

The EPS prompt must be directly runnable from the scored repository root and must state the bounded outcome, live context, authority boundaries, acceptance criteria, verification, evidence to preserve, and exact return contract. Tailor it to the selected Codex CLI or Claude Code CLI model using the frozen route supplied by the operator. Do not package unrelated Phases, task-code changes, or private evaluator material.

The ZIP is a transport copy of canonical durable state, not a competing workflow surface. The operator imports its workflow overlay into the surviving scored repository before execution. If the package is rejected before import, correct the package and return a replacement for the same unexecuted handoff. After any successful import or executor attempt, do not replay the same package: integrate returned evidence into the same canonical Phase and create a new handoff ID and new EPS instance for an ordinary retry unless the actual Phase objective or contract changed materially.
