# Full Research Prompt Template

{{WORKFLOW_CONTEXT}}

## Role

Act as a coordinated research team. Research is decision support only and cannot be treated as
implementation or result evidence.

## Project decision to inform

<!-- Name the exact later decision that research must change. -->

## Repository context

Use the managed block as the authority for root, phase, research level and routing.

```yaml
rough_input: |
  {{ROUGH_INPUT}}
```

## Required reading

- current phase contract and prompt graph;
- verified prior evidence;
- local architecture and implementation constraints;
- existing research reports and source matrix.

## Research questions

1. <!-- precise question -->
2. <!-- competing methods/evidence -->
3. <!-- implementation/compute implications -->
4. <!-- publication or risk implications -->

## Source strategy

Prioritize primary papers, official documentation, original datasets and source code. Inspect
appendices and contradictions. Distinguish external fact, source interpretation, synthesis,
implementation recommendation and uncertainty.

## Required comparison

| Candidate | Evidence quality | Assumptions | Implementation difficulty | Compute | Risk | Recommendation |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

## Required output

One integrated report with inline citations, source matrix, ranked recommendation, fallback decision
tree, exact phase/prompt implications and open local questions.

## Prohibited

No repository implementation, fictional result, unverified quote, public release or claim that a
recommended method has been executed.
