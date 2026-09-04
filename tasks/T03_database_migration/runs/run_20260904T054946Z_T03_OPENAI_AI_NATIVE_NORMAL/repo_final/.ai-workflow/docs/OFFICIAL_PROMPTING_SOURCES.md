# Official Prompting Source Lock

**Refresh date:** 2026-09-01  
**Policy:** The runtime stores distilled operational rules, not full copies of provider webpages. URLs, titles, dates, and extracted implications are retained for audit. Provider documentation may change; refresh before a major runtime release.

## OpenAI

### Model guidance — GPT-5.6

- URL: https://developers.openai.com/api/docs/guides/latest-model
- Applies to: `PROMPTING_CORE.md`, `GPT56_ROUTING.md`, `CODEX_EXECUTION.md`
- Distilled implications:
  - favor leaner prompts and state instructions once;
  - expose only relevant tools with precise descriptions;
  - define autonomy and approval boundaries compactly;
  - give goal, context, constraints, required evidence, success criteria, and output format;
  - do not prescribe every step when the route is not contractual;
  - specify tool concurrency, retries, stopping limits, and final answer requirements;
  - evaluate resource reductions only when quality/evidence remains acceptable.

### ChatGPT prompting

- URL: https://learn.chatgpt.com/docs/prompting
- Applies to: Main and general user-facing prompts
- Distilled implications:
  - structure larger tasks around goal, context, output, and boundaries;
  - include only components that materially matter;
  - leave room for the model to choose and adjust the process;
  - specify what a useful result must contain.

### Reasoning best practices

- URL: https://developers.openai.com/api/docs/guides/reasoning-best-practices
- Applies to: Main, Theory, Experiment, Verifier
- Distilled implications:
  - use simple, direct prompts;
  - avoid demanding visible chain-of-thought;
  - use clear delimiters and explicit success criteria;
  - start without unnecessary demonstrations and add examples only for measured gaps.

### Codex prompting

- URL: https://developers.openai.com/codex/prompting
- Applies to: `CODEX_EXECUTION.md`
- Distilled implications:
  - identify desired behavior, relevant code/failure, constraints, and verification;
  - let the coding agent inspect and choose implementation details where appropriate;
  - keep repository instructions and acceptance concrete.

## Anthropic

### Prompting best practices

- URL: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
- Applies to: `CLAUDE_EXECUTION.md`
- Distilled implications:
  - be clear and direct;
  - structure complex prompts and use XML sections when useful;
  - use examples selectively;
  - guide parallel calls and subagent use rather than forcing them everywhere;
  - use subagents for parallel, isolated, independent workstreams;
  - work directly for simple/sequential/shared-context work;
  - avoid over-aggressive repeated prompting.

### Parallel tool use

- URL: https://platform.claude.com/docs/en/agents-and-tools/tool-use/parallel-tool-use
- Applies to: `ORCHESTRATOR.md`, `CLAUDE_EXECUTION.md`
- Distilled implications:
  - independent read-only operations are generally suitable for parallel execution;
  - side effects, shared state, and ordering requirements may require serial execution;
  - batch only genuinely independent calls;
  - preserve correct tool-result message structure in API integrations.

### Claude Code best practices

- URL: https://code.claude.com/docs/en/best-practices
- Applies to: `CLAUDE_EXECUTION.md`
- Distilled implications:
  - use project instructions and bounded tasks;
  - subagents are useful for large reading/investigation/verification work;
  - worktrees and separate sessions reduce write collisions;
  - inspect and validate integrated results;
  - maintain external state and clean temporary artifacts.
