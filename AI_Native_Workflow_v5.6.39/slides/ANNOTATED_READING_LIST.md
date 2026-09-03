# Annotated Reading List - Mechanisms Behind AI-Native Research Workflows

This list supports the Education resource by connecting individual recent research mechanisms to the broader workflow. AI Native Workflow is presented as an adaptable synthesis, not as a claim that any one mechanism below is new.

## ReAct - Yao et al., ICLR 2023

Interleaves reasoning and environment actions. Workflow connection: research execution increasingly changes external state, so continuity cannot live only in a final text response.

## Reflexion - Shinn et al., NeurIPS 2023

Uses feedback and episodic memory to improve later trials. Workflow connection: feedback becomes more useful when the next attempt is tied to durable state and prior evidence rather than an unstructured retry.

## Language Agent Tree Search (LATS) - Zhou et al., ICML 2024

Unifies planning, acting, search, and feedback. Workflow connection: branching trajectories motivate explicit priority, merge points, and recovery boundaries.

## LLMCompiler - Kim et al., ICML 2024

Compiles dependent tool calls into a task DAG and exploits parallelism. Workflow connection: DIC/PLAN similarly makes dependencies and safe parallel execution explicit at a durable Phase level, while the coding Orchestrator realizes the current attempt.

## SWE-agent - Yang et al., NeurIPS 2024

Shows how the agent-computer interface materially affects autonomous software-engineering performance. Workflow connection: a model is only one part of an operational surface containing tools, context, files, permissions, and feedback.

## AgentDojo - Debenedetti et al., NeurIPS 2024

Evaluates prompt-injection attacks and defenses in environment-grounded tool-use settings. Workflow connection: permissions, evidence surfaces, and verifier coverage remain explicit limitations of any long-horizon agent workflow.

## Automated Design of Agentic Systems - Hu et al., ICLR 2025

Searches over agentic scaffolds. Workflow connection: prompts, tools, and agent graphs themselves are design objects; durable contracts help distinguish a changed execution realization from a changed scientific objective.

## Build Systems à la Carte - Mokhov, Mitchell, and Peyton Jones, PACMPL 2018

Not a recent AI paper, but a useful systems bridge for selective recomputation under declared dependencies. Workflow connection: local recovery is conditional on complete dependency information.

## A Brief Account of Runtime Verification - Leucker and Schallhart, 2009

A foundational runtime-verification reference. Workflow connection: evidence checking can influence continuation and repair while a system is executing rather than merely score a terminal artifact.
