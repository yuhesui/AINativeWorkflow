# Agent-facing test repository — T05_rlMetaMazeMisc

**This directory is the actual complete repository opened in Main and in the CLI executor during testing.**

It is derived minimally from `../original_task/` to make the task locally reproducible and to separate hidden evaluator material.
For AI-Native runs, `.ai-workflow/` is present directly at this repository root and is loaded by Main before the task prompt.
For Direct runs, the harness copies the same repository while physically excluding `.ai-workflow/`.

Do not pre-create Plan/Phase/DIC/EPS state. Main creates those during the scored AI-Native trajectory.
