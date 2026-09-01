# Annotated Reading List — Verification as Execution Control

## ReAct — Yao et al., ICLR 2023

Introduces an agent pattern that interleaves reasoning and environment actions. Teaching connection: once actions produce external state, verification must inspect more than the final text response.

## Reflexion — Shinn et al., NeurIPS 2023

Uses feedback to improve later trials. Teaching connection: feedback becomes more operationally useful when its result is tied to an explicit next state and retained evidence.

## Language Agent Tree Search (LATS) — Zhou et al., ICML 2024

Unifies planning, acting, search, and feedback. Teaching connection: branching trajectories make integration and recovery boundaries explicit concerns.

## AgentDojo — Debenedetti et al., NeurIPS 2024

Evaluates prompt-injection attacks and defenses in tool-using agents through environment-grounded tasks. Teaching connection: verifier quality depends on the evidence surface and properties actually tested.

## Automated Design of Agentic Systems — Hu et al., ICLR 2025

Searches over agentic scaffolds. Teaching connection: when prompts, tools, or scaffolds are changed, reliable development requires knowing what evidence was invalidated and what must be rechecked.

## Build Systems à la Carte — Mokhov, Mitchell, and Peyton Jones, PACMPL 2018

Not a recent AI paper, but a useful systems bridge for selective recomputation under declared dependencies. Teaching connection: local recovery is conditional on complete dependency information.

## A Brief Account of Runtime Verification — Leucker and Schallhart, 2009

A foundational runtime-verification reference. Teaching connection: monitoring can influence execution while a system is running rather than only evaluate a terminal artifact.
