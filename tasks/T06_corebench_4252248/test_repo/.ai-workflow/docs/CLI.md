# CLI.md — Concise `aw` Reference

`aw` is deterministic state and prompt tooling. It is not the LLM Orchestrator.

## Core

```bash
aw help
aw init
aw update
aw status [--full|--json]
aw go [--no-advance]
aw next [--print --id <ID>|--json]
aw validate
aw verify
```

## Configuration and routing

```bash
aw config show
aw config set <key> <value>
aw models show
aw models profile <all|chatgpt_only|claude_only|custom>
aw models set-available <models...>
aw models set-surfaces <surfaces...>
aw root show
aw root set <path>
aw root auto
aw root env --name AW_REPO_ROOT
```

## Phase

```bash
aw phase init <phase> --mode goal|structured ...
aw phase current
aw phase use <phase>
aw phase close --actor verifier --evidence verification/final.md
aw phase append ...
aw phase plan-next <phase> ...
```

`aw verify` is a compatibility alias for `aw validate`. Creating a next phase requires the current
phase to be explicitly closed by Verifier; proposal-only `phase plan-next` remains available before
closure.

## Requests

```bash
aw request add --text "..." --acceptance "..."
aw request list
aw request block --id RQ-001 --reason "..."
aw request reopen --id RQ-001 --reason "..."
aw request verify --id RQ-001 --actor verifier --evidence verification/file.md
```

## Prompts

```bash
aw prompt add ...
aw prompt list
aw prompt next
aw prompt set --id 02 --status running
aw prompt set --id 02 --status completed --evidence logs/02.md
aw prompt set --id 02 --status integrated --actor orchestrator --evidence logs/02.md
aw prompt set --id 02 --status verified --actor verifier --evidence verification/02.md
aw prompt supersede --id 02 --replacement 02A --reason "..."
```

## Minor

```bash
aw minor init
aw minor add
aw minor from-user --input "..."
aw minor show
aw minor note
aw minor approve
aw minor done
aw minor promote
aw minor status
aw minor sample
```

## Exit behavior

Success is zero. Contract/config/path/state errors are nonzero and should be preserved in logs.
Read-only commands must not create phases or Minor lanes. Mutating commands use atomic writes where
implemented. See the human `guides/WORKFLOW_CLI.md` for full side-effect and schema documentation.
