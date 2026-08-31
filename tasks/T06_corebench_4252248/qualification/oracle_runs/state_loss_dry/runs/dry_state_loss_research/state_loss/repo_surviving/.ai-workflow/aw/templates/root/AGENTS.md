# AGENTS.md — {{PROJECT_NAME}}

{{WORKFLOW_CONTEXT}}

## Repository authority

The managed configuration block above is the repository-root authority. Resolve and reconfirm it
before acting:

```bash
aw root show
aw status --full
aw models show
```

Do not assume the current working directory, package installation directory, or a previous chat's
path is the active repository.

## Machine workflow authority

The only machine-installed workflow root is:

```text
.ai-workflow/
```

Role guides:

| Role | Required guide |
|---|---|
| Main | `.ai-workflow/docs/MAIN.md` |
| Orchestrator | `.ai-workflow/docs/ORCHESTRATOR.md` |
| Worker | `.ai-workflow/docs/WORKER.md` |
| Minor | `.ai-workflow/docs/MINOR.md` |
| Verifier | `.ai-workflow/docs/VERIFIER.md` |
| Researcher | `.ai-workflow/docs/RESEARCH.md` |

Prompt authors also read `.ai-workflow/docs/PROMPTING_CORE.md` and, for major prompts,
`.ai-workflow/docs/MAJOR_PROMPT_REFERENCE.md`.

## Authority order

1. Current user instruction and exact approvals.
2. Repository safety, legal, security and data boundaries.
3. Current phase Goal or Structured contract.
4. Verifier-confirmed acceptance and gate evidence.
5. Active prompt and registry metadata.
6. Role, execution-level and provider guides.
7. Examples and legacy material.

A lower layer may not silently override a higher layer.

## Modes

```text
Goal Mode       Main writes one complete GOAL.md; Orchestrator plans and generates prompts as an EPS.
Structured Mode Main writes the full phase, request, plan, contract and prompt package.
Minor lane      Always phase-local and parallel only when file-disjoint and non-architectural.
```

## Evidence rule

Distinguish:

```text
planned
configured
implemented
smoke
pilot
locked
verified
```

Also record the actual backend kind:

```text
fixture | smoke | real | resource_qualification
```

A fixture is never a pilot merely because the command or filename says pilot.

## GO and continuation

After exact GO is present, Main records it immediately and does not ask again. Orchestrator then
continues through safe dependency-ready work. Only a critical blocker, material scope change, new
external/costly/destructive authority, or formal Verifier failure returns control to Main.

## Configuration refresh

After changing `.ai-workflow/config.toml`, run:

```bash
aw update
aw status --full
aw validate
```

`aw update` refreshes config-managed context in safe prompts. Terminal prompt evidence remains
historical unless an explicit include-frozen update is deliberately requested.
