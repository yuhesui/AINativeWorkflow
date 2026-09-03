# Install AI Native Workflow into a Repository

1. Copy the entire `.ai-workflow/` directory into the target repository root.
2. Do not copy individual runtime files piecemeal.
3. Start a persistent Main chat and ask it to read `.ai-workflow/docs/CORE.md`, `.ai-workflow/docs/MAIN.md`, and the repository state.
4. Main proposes the next whole Phase and one DIC.
5. Give the approved whole Phase/DIC to a repository-aware coding-agent Orchestrator such as Codex or Claude Code.
6. Review the evidence/handoff at material boundaries.

The surrounding development distribution is not runtime input unless explicitly imported.
