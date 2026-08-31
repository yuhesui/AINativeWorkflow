> **Compatibility document (v5.6.35):** retained for older v5.6.31 Goal/Structured usage. For new long-horizon work, the canonical architecture is defined by `.ai-workflow/docs/PHASE_DIC_EPS_STRUCTURE.md` and `.ai-workflow/STATE.json`.

# Migration to AI-Native Workflow v5.6.31

## From v5.6.15

1. Preserve the original four hidden roots and repository phase evidence.
2. Copy the new `.ai-workflow/` machine root.
3. Run `aw migrate --dry-run`; review; then `--execute` if appropriate.
4. Run `aw init` to create/update root controls without overwriting existing files.
5. Configure mode, levels, root, routing profile and available models/surfaces.
6. Run `aw update --all-phases --dry-run` before updating safe prompts.
7. Validate each active phase.

Concept mapping:

| Earlier concept | v5.6.31 |
|---|---|
| one Main doing everything | Main intent + Orchestrator runtime |
| Light/Standard profile | Goal/Structured Mode |
| execution Max | XHigh; Max reserved for research |
| four `.ai-workflow-*` roots | one `.ai-workflow/` root |
| long `workflow_cli.py` invocation | `aw` |
| secondary Minor | first-class phase-local Minor |
| prose requests | verifier-completed checklist |

## From experimental v5.7/v5.8 packages

- rename package/runtime to v5.6.31;
- retain only Goal/Structured; Minor phase-local;
- use `package.json` plus `config.toml` and template manifest;
- use `aw init` and `aw update` managed-context workflow;
- use GPT-5.6 routing profiles;
- keep human guides/report/slides outside machine root;
- preserve old package as rollback until tests and phase validation pass.

## Rollback

Do not delete old workflow files until the new CLI, templates, active phases and prompt context have
been validated. Migration is non-destructive by default.
