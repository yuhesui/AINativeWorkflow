# Conditions

## Direct

For T1–T4, Main receives the frozen task and permitted tools/models unless a task-specific revision says otherwise. For T6, Direct has no Main inference: one complete approved-Goal prompt opens the fixed Sol-medium Codex controller directly. Direct may plan, delegate, test, revise, and create ordinary notes, but it is **not** given `.ai-workflow/` or AI-Native instructions.

## AI-Native

Main starts in the task repository containing `.ai-workflow/`. It first loads the runtime using the frozen loader prompt. The user then supplies the same frozen task prompt. Main must treat it as the approved Goal and autonomously create the Plan, Phases, DIC views, EPS instances, evidence, and repair/replan state as warranted.

The experiment does not prescribe the number of Phases. Realized Phase count is observational data.

For T6, Main may outline the full likely Phase sequence initially but fully materializes only the current active Phase. Completed Phase evidence may return through the fixed continuation prompt for accept/repair/replan/next-Phase decisions.
