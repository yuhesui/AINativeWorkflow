# GPT56_ROUTING.md — Model and Surface Routing

## Profiles

### all

- Main major decisions: GPT-5.6 Pro, persistent ChatGPT-style session.
- Research: GPT-5.6 Pro/Deep Research.
- Orchestrator: preferred Opus 4.8, Sonnet 5, Sonnet 4.6 or GPT-5.6 Sol depending availability.
- Complex Worker: Sonnet 5/4.6 High, Opus where justified, or GPT-5.6 Terra.
- Worker: Sonnet 4.6/5 or Terra.
- Minor: Luna or an economical Sonnet/Terra route.
- Verifier: GPT-5.6 Pro fresh context or independent Opus-class run.

### chatgpt_only

- Main/Verifier: GPT-5.6 Pro; fallback Sol with max reasoning.
- Orchestrator: Sol high, fallback Terra high.
- Worker: Terra medium/high.
- Minor: Luna low.

### claude_only

- Main/Verifier: preferred Opus-class chat/fresh context.
- Orchestrator: Opus or Sonnet high.
- Worker: Sonnet medium/high.
- Minor: lowest available Claude route passing deterministic checks.

### custom

User supplies role candidates in the package/config extension. Validation requires every role to
resolve or be marked unavailable.

## Availability

`package.json` stores preference labels. `config.toml` stores declared available models/surfaces.
Use:

```bash
aw models set-available gpt-5.6-pro claude-sonnet-4.6
aw models set-surfaces chatgpt claude_code codex copilot_cli
aw models show
aw update
```

Availability is user/runtime-declared, not provider verification. Prompt logs record actual model,
interface, reasoning/effort and permission mode when the surface exposes them.

## Escalation

Escalate for semantic ambiguity, coupling, repeated incorrect repairs, science/architecture or
high-impact verification. Do not escalate merely because a temporary directory or network call
failed. Use the lowest sufficient model for deterministic Minor work.

## Main chat preference

Main benefits from conversational continuity and user interaction. Do not automatically dispatch
Main through a noninteractive coding CLI. Repository execution remains with Orchestrator/Workers.
