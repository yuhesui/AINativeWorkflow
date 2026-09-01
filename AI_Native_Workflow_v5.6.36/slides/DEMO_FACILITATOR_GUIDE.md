# Facilitator Guide — Deterministic Repair-to-Accept Demo

## Purpose

Demonstrate that a verification result can change execution while retaining only conditionally valid work.

## Run

From a repository containing `.ai-workflow/`:

```bash
python .ai-workflow/aw.py --root /tmp/aw-demo-repo demo \
  --workspace /tmp/aw-demo-repo \
  --output demo_trace.json
```

## Ask before showing the result

- Should the full workflow restart?
- Which artifact actually changed?
- Which node reads it directly?
- What assumptions justify keeping any prior evidence?

## Expected trace

```text
verification sequence: repair → accept
DIC: unchanged
EPS attempt 1: 7 nodes
EPS attempt 2: normalize + experiment + table + paper + release
retained: collect + theory
fresh-store recovery: ok=true
```

## Teaching warning

The demo establishes structural mechanics under declared dependencies. It does not establish comparative agent performance, verifier correctness in open-ended settings, or automatic dependency discovery.
