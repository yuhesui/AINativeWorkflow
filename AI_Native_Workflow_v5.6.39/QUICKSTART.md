# Quick Start — AI Native Workflow 5.6.39

## 1. Copy the runtime

Copy the whole directory into your repository root:

```text
.ai-workflow/
```

Do not copy runtime files one by one.

## 2. Start Main

Open a persistent ChatGPT/Claude-style chat and ask it to read:

```text
.ai-workflow/docs/CORE.md
.ai-workflow/docs/MAIN.md
```

Then give it access to the repository and your research/project objective. Main should recover existing package state before relying on chat memory.

## 3. Let Main propose one whole Phase

Main may request Research, Theory, or Experiment support if it can materially improve the decision. It then proposes exactly one Phase DIC **and the initial EPS/prompt graph**. The DIC contains:

```text
DIC/README.md
DIC/REQUESTS.md
DIC/PLAN.md
```

Review the Primary Aim, evidence targets, sequence/parallelism, human/material gates, and the initial EPS prompt graph. Main should package the Phase so it can be imported into the target repository.

## 4. Import and execute the whole Phase

When Main returns a self-contained Phase ZIP, import it from the target repository with:

```bash
python .ai-workflow/aw.py --root . phase import MAIN_PHASE.zip
```

This installs the Phase below root `phases/<phase_id>/`, including the DIC, Main-authored initial EPS, compact reports/evidence scaffold, and Orchestrator starter. Then use a repository-aware coding surface such as Codex or Claude Code. The Orchestrator validates the initial EPS, compiles/tunes its prompts for the actual model/surface, schedules bounded Workers/subagents, executes tools/tests/experiments, integrates evidence, and may create bounded repair EPS revisions under the unchanged DIC.

## 5. Review the handoff

Human attention should be required mainly for material scientific decisions, unexpected evidence, claim boundaries, security/external actions, and closure—not for manually scheduling every AI turn.

## Learn more

- compact runtime rules: `.ai-workflow/docs/`
- detailed guide: `.ai-workflow/guides/DETAILED_WORKFLOW_GUIDE.md`
- detailed technical report: `technical_report/AI_NATIVE_WORKFLOW_TECHNICAL_REPORT.pdf`
