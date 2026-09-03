# OpenReview Submission Metadata

## Title

Verification-Gated Hierarchical Execution: A Demo for Long-Horizon Agents

## Keywords

agent verification, long-horizon agents, runtime verification, hierarchical execution, evidence lineage, dependency-local recovery

## TL;DR

A runnable demo of a verification-gated hierarchical agent harness turns evidence checks into execution control, enabling bounded repair and dependency-scoped re-execution while preserving unaffected validated work.

## Abstract

Long-horizon agents can fail after many locally plausible steps: a completion is unsupported, an intermediate artifact becomes stale, or a repair silently invalidates downstream work. Post-hoc scoring identifies some failures but leaves execution control unresolved: what was checked, what evidence supports it, and where should execution resume? We present a runnable, package-resident agent harness in which persistent intent is refined through Goal → Plan → Phase → durable intent contract (DIC) → disposable execution prompt stack (EPS) → Prompt/Run → Action, actions bind to evidence, and verification is a control signal with four outcomes: accept, repair, replan, or escalate. The implementation records recoverable lineage and lets a failed phase instantiate a new bounded execution stack while preserving its durable contract. In a deterministic worked demo, a failed producer is repaired; its changed output invalidates four declared downstream nodes; two unaffected nodes retain prior evidence; and re-verification accepts the repaired run. Fresh-store recovery reconstructs and validates the persisted hierarchy. Under complete dependency declarations and version-bound evidence, a compact locality theorem characterizes when unaffected work can be safely retained. The demonstrated results show how evidence-gated verification can serve as a closed-loop control mechanism for bounded recovery in long-horizon agent execution.

## Relevance to Workshop

This demo gives the Who Verifies the Agents? community an inspectable implementation of verification as execution control for long-horizon agents. The harness persists phase intent, binds actions to evidence, and routes verification outcomes to accept, repair, replan, or escalate. Its deterministic recovery trace shows a failed producer triggering bounded repair and re-execution over the declared downstream dependency cone while unaffected validated evidence is retained. The anonymous `.ai-workflow` supplement makes the mechanism directly runnable and supports discussion of runtime verification, provenance, recovery boundaries, and reliable agent scaffolds.

## Supplementary Material

Attach `Who_Verifies_Agents_2026_Anonymous_AI_Workflow_Supplement.zip`. The archive contains a cleaned, double-blind `.ai-workflow/` implementation with the runnable hierarchy, DIC/EPS schemas and templates, verification/recovery logic, the deterministic worked demo, and directly relevant checks. Private project state, manuscript history, author-identifying material, credentials, caches, and unrelated CLI correctness machinery are excluded.
