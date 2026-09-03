# Prompting and Model/Surface Adaptation

Every model-executed EPS prompt is compiled from the active DIC and current evidence, then adapted to the actual model/surface.

```text
DIC + evidence
  -> docs/PROMPTING_CORE.md
  -> provider/model overlay
  -> execution-surface overlay
  -> bounded prompt
  -> audit
```

OpenAI/Codex uses `GPT56_ROUTING.md` + `CODEX_EXECUTION.md` where applicable. Claude/Claude Code uses `CLAUDE_EXECUTION.md`. Generic templates are scaffolds, not final prompts.

Prefer bounded prompts and explicit subagent decomposition when dependency/evidence boundaries justify it; avoid micro-prompts for individual shell commands.
