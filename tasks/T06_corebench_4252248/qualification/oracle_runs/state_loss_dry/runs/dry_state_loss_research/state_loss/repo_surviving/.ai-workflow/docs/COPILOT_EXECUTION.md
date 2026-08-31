# COPILOT_EXECUTION.md — GitHub Copilot CLI Operating Pattern

Copilot CLI may host Orchestrator or Worker when it supports the configured model and permission
surface.

## Required checks

- inspect local CLI help and available models;
- record selected model and reasoning controls;
- constrain allowed and denied tools;
- pass a complete generated prompt;
- preserve output and diff;
- do not assume provider model names from `package.json` are available.

## Planning versus execution

Use planning for repository mapping and prompt validation; use execution only after phase approval
and prompt readiness. If the CLI cannot preserve the required evidence or permission boundary,
fall back to another surface rather than lowering the workflow contract.

## Noninteractive work

When using a programmatic/noninteractive mode, disable unbounded user-question loops and return a
structured result to Orchestrator. Any material ambiguity goes back to Main.

## Evidence

Record actual model, tools/permissions, commands, files, tests, backend identity and caveats. The
Copilot session does not formally verify its own acceptance.
