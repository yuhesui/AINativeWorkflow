# Two-Page Education Submission — Content Outline

## Working title

**From Feedback to Recovery: Teaching Verification as Execution Control for Long-Horizon Agents**

## 1. Concept

Modern agents interleave language-model decisions, tool calls, environment feedback, and multi-step artifacts. Verification is often introduced as final scoring. This resource teaches a newer systems view: verification can be an execution-time control signal that selects among acceptance, bounded repair, upward replanning, and escalation. It also teaches the durable/disposable split between persistent intent and replaceable execution attempts, and the conditional logic of retaining work outside a declared dependency impact cone.

## 2. Level and prerequisites

Suitable for advanced undergraduates, graduate students, early-stage researchers, educators, and first-time NeurIPS attendees. Learners should recognize language-model agents, simple dependency graphs, and software tests; no runtime-verification theory is assumed.

## 3. Learning objectives

Learners will distinguish output/evidence/integration/acceptance; select one of four verification outcomes; trace a changed intermediate artifact through a dependency graph; state the assumptions required for local retention; and design a bounded verifier/recovery rule for a new agent task.

## 4. Linked papers

- Yao et al., ReAct, ICLR 2023.
- Shinn et al., Reflexion, NeurIPS 2023.
- Zhou et al., Language Agent Tree Search, ICML 2024.
- Debenedetti et al., AgentDojo, NeurIPS 2024.
- Hu et al., Automated Design of Agentic Systems, ICLR 2025.

These establish active frontier use of acting, feedback, search/planning, environment-grounded evaluation, and scaffold optimization. The resource connects them through the execution-control role of verification.

## 5. Teaching materials

An original modular slide deck; a CPU-only deterministic repair-to-accept demo; a dependency-cone learner exercise and instructor solution; an accessible facilitator guide; and an annotated reading list. A short-talk cut and self-guided path will be provided.

## 6. Scope and limitations

The deterministic demo teaches structure, not comparative performance. Safe retention assumes complete declared dependencies, version-bound evidence, deterministic-or-reverified execution, and no hidden mutable state. Open-ended verifier correctness remains an external problem and a discussion topic.
