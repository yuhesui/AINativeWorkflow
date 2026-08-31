# Main state-loss protocol

State loss means the root Main conversation is terminated and cannot be consulted again.

## Mandatory

- T5m, T6m, T7m: trigger at the first stable Main↔executor handoff after 50% of the fixed run budget.

## Optional

- T3m: after checkpoint 3/5, before checkpoint 4 is revealed.
- T4m: after checkpoint 4/8, before checkpoint 5 is revealed.

## Survives

- repository/filesystem
- Git history created during the run
- completed experiment/code artifacts
- `.ai-workflow/` durable state in AI-Native condition
- ordinary files voluntarily created by Direct

## Does not survive

- prior Main transcript
- hidden platform memory intentionally carried from the old chat
- human-written handoff
- post-hoc explanation of what the previous Main intended

Fresh Main receives the original task prompt, current repository snapshot, same permitted resources, and the frozen recovery instruction only.
