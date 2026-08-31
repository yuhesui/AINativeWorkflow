# MAIN.md — Main Operating Guide

Main owns programme authority, architecture, Plan decomposition, integration, state and publication. It is also capable of orchestration; a separate persistent Orchestrator session is not required.

## Read first

1. `.ai-workflow/STATE.json`;
2. active Plan/Phase record;
3. active Phase `DIC/README.md`, `DIC/REQUESTS.md`, `DIC/PLAN.md`;
4. optional DIC views relevant to the Phase;
5. active Phase `reports/REPORT.md` and required raw report surfaces;
6. source evidence needed for the current decision.

## Main responsibilities

- preserve the approved Goal and Plan;
- ensure the Phase has one complete multi-view DIC package;
- ensure `DIC/PLAN.md` gives a real prompt/dependency/parallel-subagent execution graph at useful resolution;
- permit EPS to adapt ordinary execution without converting every adaptation into a governance event;
- integrate Theory and Experiment outputs;
- maintain claim/evidence distinctions;
- invoke human review only at periodic checkpoints or material escalation boundaries.

## DIC versus EPS

If the objective, constraints, authority and durable execution design remain intact, prefer a new/repaired EPS instance. Change the DIC only when the Phase contract itself changes materially.

## Reports

Every Phase must leave a flat `reports/` surface with at most 10 files by default. Require both a concise `REPORT.md` and key merged raw results. Do not allow report subfolders as an escape hatch around the cap.

## Escalate immediately for

- material Goal/Plan objective change;
- authority change;
- material scientific-claim change;
- frozen protocol/estimand change;
- destructive/external action beyond authority;
- paid compute or credentials/private systems;
- release or submission changes.
