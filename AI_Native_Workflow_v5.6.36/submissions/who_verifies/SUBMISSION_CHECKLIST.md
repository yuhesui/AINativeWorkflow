# Who Verifies the Agents? — Submission Checklist

Status: **locally prepared; external submission not performed**.

## Format

- [x] Demo-paper framing is explicit.
- [x] Main paper is no more than four physical pages.
- [x] Double-blind author block is used.
- [x] NeurIPS 2026 workshop-style US Letter, 10pt, line-numbered layout is used.
- [x] Title and OpenReview metadata match.

## Scientific integrity

- [x] Exact hierarchy is `Goal -> Plan -> Phase -> DIC -> EPS -> Prompt/Run -> Action`.
- [x] Each Phase has exactly one multi-view DIC package.
- [x] Core DIC views are `README.md`, `REQUESTS.md`, and `PLAN.md`.
- [x] `PLAN.md` owns the durable prompt/dependency graph, including parallel subagents and merge/repair branches.
- [x] Verification outcomes are `accept`, `repair`, `replan`, and `escalate`.
- [x] The deterministic trace is not presented as comparative LLM-performance evidence.
- [x] Automatic dependency-cone scheduling is not claimed as a core-runtime feature.
- [x] The comparative C0/C1/C2/C3 benchmark remains labelled planned and unexecuted.

## Artifact

- [x] Anonymous supplement contains the cleaned `.ai-workflow/` runtime.
- [x] Deterministic `repair -> accept` demo is runnable.
- [x] Runtime tests and demo outputs are included.
- [x] No author identity, private project state, credentials, caches, or manuscript history is included in the anonymous supplement.
- [x] PDF was rendered and visually inspected after compilation.
