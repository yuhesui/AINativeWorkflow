# Learner Exercise - Formalize an Existing AI Research Workflow

## Part A - Start from an informal workflow

A researcher currently works like this:

```text
planning chat -> literature search -> coding agent -> experiments -> analysis/writing chat
```

The workflow is useful, but the researcher personally remembers which assumption is current, moves context between tools, decides what must rerun after a failure, and reads long outputs to reconstruct progress.

### Questions

1. State one **Primary Aim** for the current research Phase.
2. Name two supporting requests and one optional branch. Which should not be allowed to dilute the Primary Aim?
3. Which work can safely happen in parallel?
4. What evidence would let the researcher accept the Phase without replaying every AI interaction?
5. Name one decision that should still require human scientific judgement.

## Part B - Dependency-scoped repair

Suppose the Phase contains:

```text
collect data -> normalize data -> run experiment -> make table -> write paper
          \-> independent literature review
```

The verifier finds that `normalize data` wrote schema version 1, while the experiment contract requires version 2.

### Questions

1. Is this primarily `repair`, `replan`, or `escalate`?
2. Which node directly reads the changed normalized artifact?
3. Which downstream nodes must be reconsidered under the declared graph?
4. Which completed nodes may be retained under the locality assumptions?
5. Name one hidden dependency that would make retention unsafe.

## Instructor solution

### Part A

A strong answer keeps one scientific center of gravity. For example, Primary Aim: "Determine whether method A improves robustness over an equal-capacity baseline under a frozen evaluation protocol." Supporting requests might include a novelty audit and a matched-control experiment; an optional extension should proceed only if it strengthens/falsifies the Primary Aim. Parallelism is appropriate when evidence/file ownership is independent and a merge point is declared. The acceptance surface should summarize decisive evidence, failures, and unresolved uncertainty rather than raw transcripts. Human judgement remains necessary for material method/estimand/claim changes.

### Part B

1. `repair`, provided the schema correction does not change the accepted scientific protocol or authority.
2. `run experiment`.
3. `run experiment`, `make table`, and `write paper`, plus any later descendants such as release packaging.
4. `collect data` and the independent literature review.
5. Examples: the literature review secretly reads the normalized dataset; a shared mutable cache affects all nodes; or the evidence does not record input versions.

## Extensions

- **Constraint-objective inversion:** repeated review pushes the agents from "find the strongest correct result" to "remove every potentially criticizable claim." Ask which DIC field should reveal the drift.
- **Salience flattening:** five interesting branches receive equal effort and the primary contribution disappears. Ask the learner to re-rank them as primary/supporting/optional.
- **Material change:** the schema mismatch reveals that the registered estimand itself was wrong. The correct outcome is likely `replan`, because durable scientific intent/protocol must change rather than merely a local implementation.
