# RESEARCH.md — Decision-Support Research Guide

## 1. Purpose

Research supplies external evidence only when it can materially change a method, architecture, data choice, experiment, implementation decision, claim, venue, release, or submission decision.

Research is independent of execution intensity. It may be none, low, mid, high, or max.

## 2. Authority path

```text
Main → Research → Main reconciliation → Phase/DIC → Orchestrator execution
```

Research is advisory. It does not change the repository, bind the DIC, certify novelty, or count as implementation/experimental evidence by itself.

## 3. Required behavior

- inspect project files and immutable evidence first;
- state the exact Main decision the research must inform;
- prioritize primary papers, official documentation, original datasets, and authoritative source code;
- follow citations and inspect appendices/code when load-bearing;
- separate source claims, source interpretation, synthesis, local project evidence, recommendation, and uncertainty;
- compare conflicting evidence and explain why sources disagree;
- quantify implementation, compute, data, and verification burden;
- state fallback options and unresolved local questions;
- never claim that a recommended method has been implemented or tested.

## 4. Minimum research prompt

A Research prompt includes:

1. role/team disciplines;
2. exact project decision and immutable local context;
3. decision questions;
4. hard constraints and non-goals;
5. source hierarchy;
6. comparison framework;
7. required equations/assumptions where relevant;
8. implementation/experiment implications;
9. uncertainty and fallback;
10. final report structure;
11. explicit research-only boundary.

## 5. Return contract

Return one integrated report containing:

- decision to inform;
- executive conclusion;
- source matrix with dates and source classes;
- competing options and assumptions;
- contradictions/uncertainty;
- ranked recommendation and fallback tree;
- exact implications for Main's Phase/DIC planning;
- open local questions that cannot be answered from external sources.

## 6. Main integration

Main must record a binding decision before downstream code or scientific claims rely on the research. If later local evidence contradicts the literature recommendation, preserve both and update the decision transparently.
