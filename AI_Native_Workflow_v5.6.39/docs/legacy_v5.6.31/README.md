# AI-Native Workflow v5.6.31

AI-Native Workflow v5.6.31 is a repository-centered operating package for more autonomous AI-assisted research and production work. Its main purpose is to sustain coherent multi-hour or multi-day execution even when many bounded subagents run in parallel.

The package separates:

- **Main**: user intent, authority, Durable Intent Contracts (DICs), and material decisions;
- **Orchestrator**: runtime planning, Execution Prompt Stack (EPS) execution, routing, integration, bounded repair, and verification dispatch;
- **Worker**: bounded implementation;
- **Researcher**: optional source-grounded evidence returned to Main;
- **Minor**: small phase-local documentation or maintenance lane;
- **Verifier**: independent acceptance gate.

## Root package map

```text
AI_Native_Workflow_v5.6.31/
├── .ai-workflow/                              # machine runtime, CLI, guides, install guide, manifest report
├── AI_NATIVE_WORKFLOW_TECHNICAL_REPORT.pdf    # rendered report
├── AI_NATIVE_WORKFLOW_TECHNICAL_REPORT.tex    # canonical report source
├── README.md                                  # this file
├── QUICKSTART.md                              # human and AI starter prompts
├── VERSIONING.md                              # release lineage and naming notes
└── PACKAGE_MANIFEST.json                      # release file hashes
```

The root is deliberately flat. Most operational material is inside `.ai-workflow/` so that a target repository can copy one runtime folder and keep human-facing package guidance uncluttered.

## Start here

1. Read `QUICKSTART.md`.
2. Copy the whole `.ai-workflow/` folder into your target repository root.
3. Use one of the three starter prompts in `QUICKSTART.md`:
   - explain the workflow and wait;
   - initialize a Minor lane;
   - initialize the full workflow and choose Goal, Structured, or Minor.

Presentation-development materials are maintained separately and are not part of the final package or its manifest.

## Key operating distinction

For simple presentation purposes, the workflow exposes three parallel operator-facing entry lines:

```text
Goal Mode        Structured Mode        Minor lane
planning mode    planning mode          phase-local lane
```

The full report contains the more precise relationship: Minor is formally phase-local and may operate inside either Goal or Structured phases.

## Goal vs Structured Mode

| Dimension | Goal Mode | Structured Mode |
|---|---|---|
| Human reviews | `GOAL.md` only | Rich Durable Intent Contract (DIC) package and Main-authored Execution Prompt Stack (EPS) |
| Execution Prompt Stack (EPS) author | Orchestrator after Goal approval | Main before approval |
| Orchestrator starts from | Approved `GOAL.md` directly | Approved Durable Intent Contracts (DICs) and structured initialization prompt |
| Best for | outcome clear, route adaptive | interfaces, dependencies, tests, evidence, or rollback should be reviewed upfront |

## Optional tools

`aw init --install-support-tools` can attempt optional RTK and Caveman installation. These tools are aids, not authorities. If installation fails, the workflow continues and writes `.ai-workflow/install_status.json`.

See `.ai-workflow/INSTALLATION_GUIDE.md` for commands and cautions.
