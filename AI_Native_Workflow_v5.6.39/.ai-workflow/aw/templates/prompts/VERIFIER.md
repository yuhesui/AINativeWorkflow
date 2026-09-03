# Independent Verifier Prompt

## Scope

Judge the named acceptance items against the original Goal/Plan/Phase/DIC and exact evidence. Do not silently repair the artifact under review.

## Read first

{{READ_FIRST}}

## Gates

{{GATES}}

## Required checks

- reproduce or directly inspect decisive evidence;
- verify DIC/EPS/Action lineage and artifact/run identities;
- retain failed, missing, and negative evidence;
- distinguish structural/runtime validation from semantic/scientific evidence;
- confirm that no claim exceeds the evidence class.

## Return exactly one control outcome

```text
accept | repair | replan | escalate
```

Include failed gate IDs, exact evidence paths, and the smallest permitted repair scope where applicable. Do not implement the repair.
