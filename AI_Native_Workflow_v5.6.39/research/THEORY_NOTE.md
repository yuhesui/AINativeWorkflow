# Formal theory note

## Objects

Let the repository/environment state be a keyed state `s∈S`; a global intent is a goal predicate `G:S→{0,1}` plus admissible trace constraints. A Plan is a dependency DAG of Phase contracts. A DIC contains a bounded subgoal, precondition, invariant, acceptance predicate/set, evidence predicate, authority and escalation set. EPS is a disposable operational policy refined from one DIC. An Action is a primitive state transition and evidence emission.

## Strongest surviving results

The most mechanism-specific positive result is dependency-local recovery: complete read/write declarations and versioned evidence make the transitive impact cone a sufficient safe invalidation set, and the direct-reader seed is worst-case necessary. The imperfect-verification analysis gives an exponential tail in the number of passed gates under a conditional miss bound, and a simple checkpoint-interval optimum under a stationary cost model.

The strongest negative result is observational: when evidence aliases goal-satisfying and goal-violating states, no evidence-only verifier can eliminate both false acceptance and false rejection. Hierarchy cannot repair information absent from the verification channel.

## Novelty caution

These are correct structural results, not evidence of a new foundational theory. Contract composition, incremental rebuild locality, checkpoint/restart analysis, and partial-observability limits have deep prior literatures. The scientific opportunity is to connect them to language-agent harnesses and test whether the predicted horizon/fault-locality effects occur under matched inference budgets.
