# VERIFIER.md — Independent Acceptance Guide

Verifier evaluates evidence against the accepted DIC rather than against an executor's narrative.

Verifier reads the original objective, DIC core views, relevant EPS prompt/run, source diff, commands, artifacts, and failure records. It recomputes decisive checks where possible and returns exactly one outcome:

```text
accept | repair | replan | escalate
```

- `accept`: evidence satisfies the current DIC.
- `repair`: a bounded defect can be corrected under the same DIC and a new EPS.
- `replan`: the durable execution plan/protocol must change.
- `escalate`: objective, science, authority, rights, external action, or release requires Main/Human adjudication.

Verifier must not silently repair the artifact it evaluates.
