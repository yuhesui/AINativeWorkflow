> **Compatibility document (v5.6.35):** retained for older v5.6.31 Goal/Structured usage. For new long-horizon work, the canonical architecture is defined by `.ai-workflow/docs/PHASE_DIC_EPS_STRUCTURE.md` and `.ai-workflow/STATE.json`.

# Migration — AI-Native Workflow v5.6.31

## Supported source states

- v5.6.15 four-root repository installation;
- experimental v5.7/v5.8 one-root packages;
- repositories with no workflow runtime.

## Key changes

| Earlier behavior | v5.6.31 |
|---|---|
| Main mixes intent and runtime execution | Main intent/authority; Orchestrator runtime |
| Light/Standard | Goal/Structured Mode |
| execution Max | XHigh; Max reserved for research |
| Minor may be root/custom | Minor phase-local only |
| static prompt context | config-managed context + `aw update` |
| implicit model choice | routing profile + declared available models/surfaces |
| long CLI invocation | `aw` |
| Worker/Orchestrator self-acceptance | Verifier owns formal gates/request completion |

## Procedure

1. Create a rollback copy of workflow roots and active phase files.
2. Copy the new `.ai-workflow/` root.
3. Run `aw migrate --dry-run` for old four-root installations.
4. Run `aw init` without a phase to create/preserve root controls.
5. Configure root, mode, levels, routing and available models.
6. Review `aw update --all-phases --dry-run`.
7. Update only safe prompts; do not casually use `--include-frozen`.
8. Validate each active phase.
9. Run the workflow unit suite and one generated Goal/Structured smoke.
10. Retain the old package until new phases and installed CLI are verified.

## Legacy terms

Old Light/Standard aliases are not active CLI modes. Historical documentation may mention them only
inside migration notes. Root/custom Minor settings must be reconciled into the relevant phase.

## Rollback

Restore the preserved old roots and root routing files. Do not mix half-migrated state across two
active CLIs.
