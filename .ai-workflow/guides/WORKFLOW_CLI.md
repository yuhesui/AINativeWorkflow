> **Compatibility document (v5.6.35):** retained for older v5.6.31 Goal/Structured usage. For new long-horizon work, the canonical architecture is defined by `.ai-workflow/docs/PHASE_DIC_EPS_STRUCTURE.md` and `.ai-workflow/STATE.json`.

# WORKFLOW_CLI.md — Complete `aw` Guide for v5.6.31

## 1. What `aw` is

`aw` is a deterministic Python CLI for workflow state, prompt rendering, configuration
synchronisation, request/prompt lifecycle, phase-local Minor work, validation and migration. It is
not an LLM and does not replace Main or Orchestrator.

Both entry points are installed:

```text
aw
aw
```

`aw` is canonical; `aw` remains a compatibility alias.

`aw help` prints top-level help. `aw verify` is a compatibility alias for `aw validate`.

Global `--root` may precede or follow the subcommand.

## 2. Initialization

```bash
aw init [options]
```

Creates or preserves root `AGENTS.md`, `agent.manifest.yaml` and `phases/`. It may create a first
phase from active config.

Important options:

```text
--project-name
--phase
--mode goal|structured
--execution-level low|mid|high|xhigh|ultra
--research-level none|low|mid|high|max
--test-profile focused|affected|integration|full
--routing-profile all|chatgpt_only|claude_only|custom
--root-mode auto|fixed|environment|cwd
--declared-root
--available-model (repeatable)
--surface (repeatable)
--rough-input
--approval-phrase
```

Example:

```bash
aw init --project-name HealthFormer-RL --phase phase_01_positive \
  --mode structured --execution-level high --research-level high \
  --test-profile integration --routing-profile all \
  --declared-root D:/HealthFormer-RL \
  --available-model gpt-5.6-pro \
  --available-model claude-sonnet-4.6 \
  --surface chatgpt --surface claude_code
```

Output is one JSON document. Initial prompts contain the resolved config/model/root context.

## 3. Updating prompts from config

```bash
aw update
```

Refreshes config-managed context in planned/ready prompts, phase metadata/registry, the phase Minor
init prompt and root managed blocks. It does not regenerate task bodies or overwrite semantic
content.

Options:

```text
--phase <name>          selected/current phase
--all-phases            every phase
--dry-run               report intended changes only
--include-frozen        also update terminal prompt context metadata
--no-root-files         do not update AGENTS/manifest managed blocks
```

Use after:

- repository-root change;
- mode/level/test profile change;
- routing-profile change;
- declared available model/surface change;
- package/config migration.

Safe workflow:

```bash
aw config set routing_profile chatgpt_only
aw models set-available gpt-5.6-pro gpt-5.6-terra
aw update
aw validate
aw status --full
```

Default terminal-prompt skipping preserves historical evidence.

## 4. Status and next work

```bash
aw status
aw status --full
aw status --json
```

Reports root, mode, levels, routing, declared models, approval, requests, prompt counts/readiness,
stale contexts, Minor and phase health.

```bash
aw next
aw next --json
aw next --print
aw next --print --id 05
```

`aw next` shows prompt path, model profile, preferred/options, test profile, backend and evidence
target. It does not launch the agent.

## 5. Approval

```bash
aw go
aw go --no-advance
aw approval show
aw approval record --text "EXACT GO"
```

`aw go` uses the configured approval phrase, validates acceptance-bearing requests, and writes the
approval and scope hash. In Goal Mode it first materialises `REQUESTS.md` from real `G-###`
acceptance items and marks `GOAL` ready. In Structured Mode it marks Orchestrator prompt `000`
ready. Approval does not create or generically advance a Prompt `001`.

## 6. Repository root

```bash
aw root show
aw root set D:/Projects/Repo
aw root auto
aw root env --name AW_REPO_ROOT
```

Modes:

- auto: upward `.ai-workflow/config.toml` discovery;
- fixed: configured absolute root;
- environment: named environment variable;
- cwd: current working directory.

Generated prompts include the declared root. Agents still verify it before mutation.

## 7. Configuration and models

```bash
aw config show [--json]
aw config set <dotted.key> <value>
```

Common keys:

```text
mode
execution_level
research_level
test_profile
routing_profile
approval_phrase
repository.root_mode
repository.root
minor.approval
testing.default_profile
```

Minor location/path are intentionally not configurable.

Models:

```bash
aw models show [--json]
aw models profile all|chatgpt_only|claude_only|custom
aw models set-available <ids...>
aw models set-surfaces <surfaces...>
```

The resolver selects the first declared candidate matching a role preference; otherwise it reports
the first preference with unverified availability.

## 8. Phase commands

```bash
aw phase init phase_01 --mode goal ...
aw phase current
aw phase use phase_01
aw phase close --actor verifier --evidence verification/final.md
aw phase append --doc goal|requests|plan|readme|architecture|approval ...
aw phase plan-next phase_02 ...
```

Goal Mode creates `GOAL.md` and init prompts; Structured Mode creates requests, plan, approval,
architecture (unless disabled) and copies full templates by default.

`phase close` requires exact approval, all requests independently verified, all prompts integrated
or verified, and Verifier-owned closure evidence. `phase plan-next` always writes a proposal JSON;
`--create` requires the current phase to be closed.

## 9. Requests

```bash
aw request add --text "Outcome" \
  --acceptance "Criterion 1" --acceptance "Criterion 2"
aw request list
aw request block --id RQ-001 --reason "..."
aw request reopen --id RQ-001 --reason "..."
aw request verify --id RQ-001 --actor verifier --evidence verification/final.md
```

Only Verifier may verify. Markdown checkboxes and event evidence must agree.

## 10. Prompt registry

```bash
aw prompt add --id 02 --title "..." --depends-on 001 \
  --model-profile worker --execution-level mid --test-profile affected \
  --backend real --evidence-level implementation \
  --allowed "src/**,tests/**" --forbidden ".git/**,archive/**" \
  --output src/module.py --check "pytest tests/module"
```

Lifecycle:

```bash
aw prompt set --id 02 --status running
aw prompt set --id 02 --status completed --evidence logs/02.md
aw prompt set --id 02 --status integrated --actor orchestrator --evidence logs/02.md
aw prompt set --id 02 --status verified --actor verifier --evidence verification/02.md
```

Supersession:

```bash
aw prompt supersede --id 02 --replacement 02A --reason "path contract repair"
```

Downstream dependencies wait for replacement integration.

## 11. Minor

```bash
aw minor init
aw minor add --type fix --title "..." --request "..." ...
aw minor from-user --input "fix links and update status"
aw minor show [--id MF-01]
aw minor note ...
aw minor approve --id MF-01 --confirmation "GO MinorFix 01"
aw minor done ...
aw minor promote --id MF-01 --to-prompt 07A ...
aw minor status
aw minor sample --type fix --rough-input "..." --write <path>
```

Minor is always phase-local. Completion requires evidence/log. Promotion preserves history and
creates a normal prompt.

## 12. Validation

```bash
aw validate
aw validate --json
```

Checks mode-specific files, acceptance, request/verifier events, prompt IDs/dependencies/lifecycle,
config/frontmatter parity, managed context freshness, path/output contracts, supersession,
approval/scope hash, phase-local Minor and reports allowlist.

Warnings do not fail exit status; errors return nonzero.

## 13. Migration

```bash
aw migrate --dry-run
aw migrate --execute
```

Moves older four-root workflow directories under `.ai-workflow/legacy/pre_v5.6.30/` without
silently deleting them. Review migration plan and back up before execution.

## 14. Atomicity and evidence

State files use atomic writes where implemented; event files are append-only JSONL. High-risk
repositories should coordinate concurrent writers externally or extend revision locking. CLI
stdout is concise/JSON; decisive execution evidence belongs in prompt logs, not only terminal
history.
