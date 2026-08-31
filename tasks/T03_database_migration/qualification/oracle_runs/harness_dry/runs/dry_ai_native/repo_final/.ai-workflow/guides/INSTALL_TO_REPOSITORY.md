> **Compatibility document (v5.6.35):** retained for older v5.6.31 Goal/Structured usage. For new long-horizon work, the canonical architecture is defined by `.ai-workflow/docs/PHASE_DIC_EPS_STRUCTURE.md` and `.ai-workflow/STATE.json`.

# Install AI-Native Workflow v5.6.31 into a Repository

## 1. Back up existing workflow controls

Preserve any existing `.ai-workflow*`, `AGENTS.md`, `agent.manifest.yaml` and active phase files.
Do not replace an active workflow without a rollback copy.

## 2. Copy the machine root

Copy only:

```text
.ai-workflow/
```

from this distribution to the repository root. Human guides, report and slides do not need to be
installed into every project.

## 3. Verify source wrapper

```bash
python .ai-workflow/aw.py --version
python .ai-workflow/aw.py --help
```

Expected version:

```text
5.6.31
```

## 4. Optional editable install

```bash
python -m pip install -e .ai-workflow
aw --version
```

## 5. Initialize

```bash
aw init --project-name "Project" \
  --phase phase_01_goal \
  --mode goal \
  --routing-profile all \
  --available-model gpt-5.6-pro \
  --surface chatgpt
```

Use `--declared-root` or `aw root set` when a fixed root should be embedded into prompts.

## 6. Validate configuration and generated prompts

```bash
aw root show
aw config show
aw models show
aw status --full
aw validate
```

After any configuration change:

```bash
aw update
aw validate
```

## 7. Migration from older roots

```bash
aw migrate --dry-run
aw migrate --execute
```

Review the plan first. Older roots are moved under `.ai-workflow/legacy/pre_v5.6.30/`, not deleted.

## 8. Installation boundary

Installation does not authorize project mutation, private-data movement, external tools, paid
compute, release or submission. Those belong to the active phase contract and exact user approval.
