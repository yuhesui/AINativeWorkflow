# Machine Runtime Manifest Report

**Version:** 5.6.35  
**Canonical state:** `.ai-workflow/STATE.json`  
**Current approved Plan:** `plan-workshop-poc-evaluation`  
**Next machine Phase:** `phase-01-engineering-release-env` (prepared/pending)

The runtime uses Goal → Plan → Phase → one multi-view DIC → EPS → Prompt/Run → Action. Reports are mandatory/flat/capped; optional lanes remain `off|auto|on`.

v5.6.35 is a deadline/execution-state release. It adds no scored benchmark evidence. Who Verifies is routed to a ≤4-page demo reconstruction; AutoMLR is routed to a strict eligibility/abstract audit; the targeted experiment remains the dominant missing research evidence for Meta-Agents.

Validate with:

```bash
PYTHONPATH=.ai-workflow pytest -q .ai-workflow/tests
python .ai-workflow/aw_hierarchy.py --root . recover
```
