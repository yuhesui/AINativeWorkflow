# Operations and checkpoint policy

The normal operating pattern is **exception-driven human supervision**: machines handle routine execution/coordination within an approved Phase, while human attention is requested at periodic programme checkpoints and immediate material boundaries.

## Human-attention objective

The workflow aims to lower human supervisory attention per unit of verified research progress, not to minimize human involvement indiscriminately. Checkpoints should therefore summarize only decision-relevant state: Primary Aim, accepted evidence, material uncertainty, invalidated dependencies, resource/authority changes, and the exact decision needed from the human.

A checkpoint that forces the researcher to reconstruct raw prompt histories, terminal logs, or every local repair has failed as a human interface.

## Ordinary machine loop

```text
recover Plan/Phase state
-> read the complete DIC package and Primary Aim
-> follow/refine DIC/PLAN execution graph
-> instantiate current nodes through EPS
-> run prompts/actions, often in parallel subagent batches
-> record raw evidence and logs
-> integrate key evidence into compact report surfaces
-> reconcile prioritized REQUESTS
-> accept / repair / replan / escalate
```

The human does not approve each prompt or EPS instance.

## Salience discipline

Execution should not turn every feasible branch into an equal-priority workstream. Primary requests dominate supporting work; optional branches proceed only when they plausibly strengthen or falsify the Primary Aim. Repeated auditing must not silently convert "find the strongest correct result" into "make the project maximally uncriticizable." Material changes in scientific objective return to Main/human authority.

## Checkpoints and escalation

A periodic checkpoint reviews objective drift, Primary Aim salience, evidence quality, dependency invalidation, human-attention burden, cost, unresolved scientific uncertainty, and release implications. It does not replay ordinary implementation decisions.

Immediate escalation bypasses the interval for material changes to objective, authority, scientific claim, frozen protocol, destructive/external actions, paid compute, credentials/private systems, release, or submission state.

Independent verification should be genuinely independent in provenance/context where required. Local checks and lightweight milestone rechecks need not become separate human-supervised sessions.
