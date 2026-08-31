# CLAUDE_EXECUTION.md — Claude Code Operating Pattern

Claude Code normally hosts Orchestrator or Worker, not persistent Main.

## Session setup

- start in the declared repository root;
- read the generated prompt file rather than relying on prior chat;
- select a configured available model;
- restrict tools to required read/edit/shell surfaces;
- preserve command output and diffs in the declared log;
- avoid broad permission modes unless the prompt and execution level authorize them.
- for Sonnet 5, use adaptive thinking/current effort controls rather than legacy manual thinking
  budgets, and do not set incompatible sampling controls;
- for Opus 5, state the desired outcome and evidence directly and avoid redundant
  over-verification loops.

Conceptual noninteractive pattern:

```text
claude -p <complete prompt> --model <configured model> <bounded tool permissions>
```

Exact flags vary by installed version; inspect local help and record them. Do not copy a command
from this guide without verifying support.

## Orchestrator use

Claude Code reads `ORCHESTRATOR.md`, runs `aw status --full`, `aw next` and `aw validate`, then
routes bounded Worker prompts. It may generate execution prompts in Goal Mode. It integrates only after
inspecting source, diff, commands and evidence.

## Worker use

Pass one complete prompt. Prevent unrelated refactors. Use the declared test profile. Return the
actual model/permissions when exposed.

## Permission posture

- read-only preflight first;
- allow exact edit families;
- allow named tests/build commands;
- deny release/upload/credential/destructive commands unless separately authorized;
- request user input only when the prompt says the issue is material.

## Context recovery

When a session resets, resume from phase files and prompt registry. Never rely on hidden session
memory as the only state.
