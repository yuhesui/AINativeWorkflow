# NeurIPS Education Track - Teaching Materials Plan

## Teaching objective

Provide a reusable, original resource that helps researchers formalize or improve the AI workflow they already use. The learner should be able to take an existing planning-chat / research / coding-agent practice and add durable priorities, Phase-level contracts, explicit dependencies/parallelism, evidence gates, and human escalation boundaries.

## Proposed bundle

```text
ai_native_research_workflow/
├── README.md
├── slides/
│   ├── source deck
│   ├── rendered PDF
│   └── accessible speaker notes
├── demo/
│   ├── cleaned .ai-workflow teaching runtime
│   ├── deterministic trace / CLI instructions
│   └── fixed expected trace
├── exercise/
│   ├── map-your-own-research-workflow worksheet
│   ├── instructor solution
│   └── repair / replan / escalation scenarios
├── notebook/
│   └── optional dependency-and-attention explorer.ipynb
├── references/
│   └── annotated reading list, 2022-2026
└── LICENSE / attribution
```

## Prepared live module

- 15-20 minute full deck so several slides can be removed if the assigned slot is shorter.
- Begin from an informal researcher workflow, not from DIC/EPS jargon.
- Use recurring human examples before introducing formal artifacts.
- Teach DIC as a human-comprehension interface as well as a machine contract.
- Demonstrate one dependency-scoped repair and one material change requiring replanning.

## Learning progression

1. **Recognize:** identify where an informal AI workflow currently consumes researcher coordination attention.
2. **Understand:** distinguish durable intent/Phase state from disposable execution attempts.
3. **Apply:** map one research Phase into Primary Aim, prioritized requests, dependencies, parallel branches, evidence, and human gates.
4. **Analyse:** identify defensive drift/constraint-objective inversion, salience flattening, stale dependency propagation, and false completion.
5. **Create/adapt:** redesign an existing personal research workflow using only the pieces that add value.

## Accessibility

- define DIC/EPS only after plain-language examples;
- provide alt text for every diagram;
- avoid color-only distinctions;
- include a text transcript of the worked trace;
- keep code examples runnable on CPU with no credentials or external service;
- provide both a short-talk and self-guided path.

## Integrity

Human-attention intensity is a proposed evaluation quantity, not a claim that the workflow already saves a measured amount of researcher time or effort. Deterministic demo evidence remains structural/runtime evidence.
