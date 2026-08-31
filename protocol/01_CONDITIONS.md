# Conditions

## Direct

Main receives the frozen task and the permitted tools/models. It may plan, delegate, test, revise, create ordinary notes, and work competently in whatever natural way it chooses. It is **not** given `.ai-workflow/` or AI-Native instructions.

## AI-Native

Main starts in the task repository containing `.ai-workflow/`. It first loads the runtime using the frozen loader prompt. The user then supplies the same frozen task prompt. Main must treat it as the approved Goal and autonomously create the Plan, Phases, DIC views, EPS instances, evidence, and repair/replan state as warranted.

The experiment does not prescribe the number of Phases. Realized Phase count is observational data.
