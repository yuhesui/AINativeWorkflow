# Learner Exercise — What Should Happen After Verification Fails?

## Scenario

A research agent executes:

```text
collect data → normalize data → run experiment → make table → write paper
         \→ independent literature review
```

The verifier finds that `normalize data` wrote schema version 1, while the experiment contract requires version 2.

## Questions

1. Is this primarily `repair`, `replan`, or `escalate`? Explain in one sentence.
2. Which node directly reads the changed normalized artifact?
3. Which downstream nodes must be reconsidered under the declared graph?
4. Which completed nodes may be retained under the locality assumptions?
5. Name one hidden dependency that would make retention unsafe.

## Instructor solution

1. `repair`, provided the schema correction does not change the accepted scientific protocol or authority.
2. `run experiment`.
3. `run experiment`, `make table`, and `write paper`, plus any later descendants such as release packaging.
4. `collect data` and the independent literature review.
5. Examples: the literature review secretly reads the normalized dataset; a shared mutable cache affects all nodes; or the evidence does not record input versions.

## Extension

Change the failure: the schema mismatch reveals that the registered estimand itself was wrong. The correct outcome is now likely `replan`, because durable scientific intent/protocol must change rather than merely a local implementation.
