# NeurIPS Education Track — Teaching Materials Plan

## Required submission bundle

The official call requires a teaching-materials ZIP below 200 MB plus a no-more-than-two-page concept PDF. The educational materials must be original and specifically prepared for the 2026 Education Track.

## Proposed bundle

```text
verification_as_execution_control/
├── README.md
├── slides/
│   ├── source deck
│   ├── rendered PDF
│   └── accessible speaker notes
├── demo/
│   ├── cleaned .ai-workflow runtime
│   ├── demo_trace.py / CLI instructions
│   └── fixed expected trace
├── exercise/
│   ├── learner worksheet
│   ├── instructor solution
│   └── four additional scenarios
├── notebook/
│   └── optional dependency-cone explorer.ipynb
├── references/
│   └── annotated reading list, 2022–2026
└── LICENSE / attribution
```

## Minimum viable original resource

1. 12–17 slide teaching deck.
2. Runnable deterministic failure-to-recovery demo.
3. One learner worksheet on the four outcomes and dependency cone.
4. Instructor guide with timing, common misconceptions, and solutions.
5. Annotated reading list with at least five frontier papers.

## Accessibility

- define DIC/EPS only after plain-language concepts;
- provide alt text for every diagram;
- avoid color-only distinctions;
- include a text transcript of the worked trace;
- keep code examples runnable on CPU with no credentials or external service;
- provide both a short-talk and self-guided path.

## Evaluation of learning

Use a three-stage check:

1. **Recall:** distinguish score, evidence, integration, and acceptance.
2. **Application:** select `repair`, `replan`, or `escalate` for a scenario.
3. **Creation:** design one verifier property and recovery boundary for a new task.

## Remaining production items

- final source slide deck and rendered PDF;
- two-page Education-track PDF in the official `education, final` template;
- optional interactive notebook;
- permanent public repository or archive link;
- author details and licenses;
- final originality and accessibility audit.
