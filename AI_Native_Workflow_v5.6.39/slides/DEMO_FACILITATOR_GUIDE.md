# Facilitator Guide - AI-Native Research Workflow Demo

## Purpose

Use one deterministic repair-to-accept trace to demonstrate a broader workflow principle: a complex AI execution history should return to the researcher as a compact, evidence-linked state transition rather than another long transcript to reconstruct.

## Context to give learners

The researcher already uses several AI surfaces. A Phase has one Primary Aim and one durable DIC. Main authors the initial EPS/prompt graph from the DIC; the coding-agent Orchestrator validates and executes it, and may create bounded repair EPS revisions. The demo intentionally focuses on the execution/repair layer, not on the entire workflow.

## Run

From a repository containing `.ai-workflow/`:

```bash
python .ai-workflow/aw.py demo --output demo_trace.json
```

## Ask before showing the result

- Should the full workflow restart?
- Which artifact actually changed?
- Which node reads it directly?
- What assumptions justify keeping any prior evidence?
- What should the human need to inspect before allowing continuation?

## Expected trace

```text
verification sequence: repair -> accept
DIC: unchanged
EPS attempt 1: 7 nodes
EPS attempt 2: normalize + experiment + table + paper + release
retained: collect + theory
fresh-store recovery: ok=true
```

## Teaching point

The researcher should receive a compact statement of what changed, what was invalidated, what was retained, and whether the scientific contract changed. They should not need to replay seven prompts and terminal histories to recover the state.

## Integrity warning

The demo establishes structural mechanics under declared dependencies. It does not establish comparative agent performance, verifier correctness in open-ended settings, automatic dependency discovery, or measured human-attention savings.
