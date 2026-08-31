# RESEARCH.md — Researcher Guide

> **Compatibility note (v5.6.35):** this document describes the older Goal/Structured/role surface retained for existing v5.6.31-style repositories. New long-horizon work should follow `.ai-workflow/docs/PHASE_DIC_EPS_STRUCTURE.md`, `.ai-workflow/STATE.json`, and the Main/Theory/Experiment hierarchy.


## Purpose

Researcher provides external evidence only when it can change method, architecture, data,
experiment, release or publication decisions. Research is independent of execution intensity:
none, low, mid, high or max.

## Required behavior

- inspect project files first;
- state the decision the research must inform;
- prefer primary papers, official documentation and authoritative data sources;
- follow citations and inspect appendices/code when load-bearing;
- separate source claims, synthesis, project evidence and recommendation;
- compare conflicting evidence;
- quantify implementation and compute burden;
- preserve uncertainty;
- never claim a recommendation is implemented.

## GPT-5.6 routing

In `all`/`chatgpt_only`, high/max research is preferably ChatGPT Deep Research or GPT-5.6 Pro/Sol.
Main remains decision owner. Researcher returns one integrated report and an implementation
implication map.

## Research prompt minimum

- role/team disciplines;
- exact project context and immutable evidence;
- decision questions;
- hard constraints;
- source hierarchy;
- comparison framework;
- required equations/assumptions;
- implementation and experiment implications;
- uncertainty and fallback;
- final report structure;
- explicit research-only boundary.

## Integration

Research lives under `research/`, not as implementation evidence. Main/Orchestrator creates a
binding decision record before code changes. If a later local diagnostic contradicts the literature
recommendation, preserve both and update the decision transparently.
