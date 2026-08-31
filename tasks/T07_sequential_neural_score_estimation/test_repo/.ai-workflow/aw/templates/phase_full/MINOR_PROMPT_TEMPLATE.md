# Full Phase-Local Minor Prompt Template

{{WORKFLOW_CONTEXT}}

## Role

Act as Minor Fixer, Updater or Reporter. The task is routine, reversible and non-architectural.
Use the cheapest configured model likely to pass deterministic validation.

## Repository and phase

Use the managed block as the authority for root, phase, model routing and phase-local Minor path.

## Preserved rough input

```text
{{ROUGH_INPUT}}
```

## Interpretation

<!-- One bounded interpretation; preserve rough input separately. -->

## Exact confirmation

```text
<GO MinorFix/MinorUpdate/MinorReport NN when required>
```

Do not infer confirmation. Phase approval may cover the task only when the ledger says
`approved_by_phase`.

## Read first

- repository instructions;
- current phase README/Goal or Plan;
- full Minor request block;
- exact files to be changed;
- `.ai-workflow/docs/MINOR.md`.

## Allowed scope

```text
<exact files>
```

## Forbidden scope

No architecture, dependencies, public interface, scientific method, experiment config, data policy,
claims, release, external action or destructive work.

## Work

1. Inspect the exact defect/update/report source.
2. Make the smallest change.
3. Run the named deterministic check.
4. Write one Minor log.
5. Close with `aw minor done`.
6. Promote with `aw minor promote` if the task proves non-minor.

## Return

```text
Minor ID:
Files read:
Files changed:
Checks:
Log:
Caveats:
Terminal status:
```
