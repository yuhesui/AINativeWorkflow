# Runtime and ignored-file reconstruction prompt

Use this prompt when maintaining or recreating this evaluation repository:

```text
Reconstruct the canonical AI-Native runtime ZIP from the currently configured
source package path in AI_WORKFLOW_RUNTIME_SOURCE.json. The current source is
AI_Native_Workflow_v5.6.36/.ai-workflow.

Treat the complete configured AI_Native_Workflow_v5.6.36 package as the tracked
authority. Write the clean deterministic runtime archive to the Git-ignored
repository-root AI_WORKFLOW_RUNTIME.zip, then install byte-identical clean
runtime copies at the repository root and in every frozen task's
test_repo/.ai-workflow directory. Reset the general/default runtime source used
by new task materialization to AI_WORKFLOW_RUNTIME_SOURCE.json. Refresh runtime,
task, aggregate, and package hashes and run the runtime tests plus full
repository validation.

Reconstruct all deterministically recoverable files that are intentionally
Git-ignored to avoid duplicate uploads. Never invent credentials, caches,
container state, raw run evidence, or mutable trajectory state. Preserve unique
handoffs, results, and complete repo_final archives. Do not execute a scored
trajectory or alter frozen task identities, state-loss rules, condition
definitions, or primary metrics.
```

Default command:

```powershell
python -X utf8 scripts/update_ai_workflow.py
```
