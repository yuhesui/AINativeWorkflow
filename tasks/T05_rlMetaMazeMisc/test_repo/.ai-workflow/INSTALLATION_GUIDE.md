# AI-Native Workflow v5.6.31 Installation Guide

This guide belongs inside `.ai-workflow/` because it supports the runtime environment. It is not a root-level human orientation document.

## Required workflow runtime

Copy the entire `.ai-workflow/` folder into the target repository root. Then check:

```bash
python .ai-workflow/aw.py --version
python .ai-workflow/aw.py --help
```

Optional editable CLI install:

```bash
python -m pip install -e .ai-workflow
aw --version
```

## Optional support tools attempted during initialization

When the user chooses the support-tool initialization path, `aw init --install-support-tools` performs a best-effort check/install for RTK and Caveman. Failures are non-fatal and are written to:

```text
.ai-workflow/install_status.json
```

Continue the workflow even when either tool fails to install; report the missing tool to the user and use ordinary terminal output or normal prompting.

## RTK terminal-output compression

RTK is optional. It compresses terminal output before it enters the LLM context. Recommended manual commands:

```bash
# macOS Homebrew
brew install rtk

# Linux/macOS quick install
curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh

# Cargo fallback
cargo install --git https://github.com/rtk-ai/rtk

# Verify
rtk --version
```

Use RTK only where compressed output does not hide decisive failure information. Rerun without RTK when raw output is needed.

## Caveman prompt/skill support

Caveman is optional prompt-behaviour support for terse agent output. Recommended manual commands:

```bash
# macOS / Linux / WSL / Git Bash
curl -fsSL https://raw.githubusercontent.com/JuliusBrussee/caveman/main/install.sh | bash

# Preview before install
curl -fsSL https://raw.githubusercontent.com/JuliusBrussee/caveman/main/install.sh | bash -s -- --dry-run

# Windows PowerShell
irm https://raw.githubusercontent.com/JuliusBrussee/caveman/main/install.ps1 | iex

# Codex CLI per-agent skill path, when npx skills is available
npx skills add JuliusBrussee/caveman -a codex
```

Caveman is not a workflow role and does not change authority. Avoid it for delicate prose, audit judgement, policy-sensitive writing, or irreversible confirmations.

## Recommended initialized command

```bash
python .ai-workflow/aw.py init \
  --project-name "<Project>" \
  --mode goal \
  --execution-level mid \
  --research-level none \
  --test-profile affected \
  --routing-profile all \
  --phase phase_01_goal \
  --install-support-tools
```

If installation fails, continue and inspect `.ai-workflow/install_status.json`.
