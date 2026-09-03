# GPT-5.6-era prompting guide

An ordinary execution brief should state the **primary outcome first**, then only the domain/package context, hard constraints, observable success/evidence criteria, authority boundary, and deliverable that materially affect the task. State each load-bearing instruction once. Let the model choose the execution route unless the route itself is frozen by the DIC.

## Salience

Prompts should preserve the DIC's Primary Aim. Supporting constraints, caveats, formatting requirements, and optional improvements must not become rhetorically equal to the primary outcome. In research work, "avoid unsupported claims" is normally a constraint on the search for the strongest correct result, not a replacement objective.

## Human-attention return contract

Return the smallest complete decision surface needed by the parent/Main:

- result against the primary outcome;
- decisive evidence and its location;
- material failures/uncertainty;
- changed artifacts;
- whether repair/replan/escalation is required.

Do not make the human reconstruct the result from long execution transcripts. Preserve full logs separately when needed for auditability.

## Provider/model adaptation

Generic templates are scaffolds. The coding-agent Orchestrator must adapt concrete EPS prompts to the actual execution model/surface using the current provider-derived guides in `.ai-workflow/docs/`, remove duplicated instructions, preserve authority/evidence requirements, and record prompt-tuning provenance before model-executed Actions.

Avoid ceremonial prompt numbering, requests for visible chain-of-thought, and repeated global warnings that dilute the primary task. Use fresh independent contexts at material evidence/claim/release boundaries or when independence itself is part of the verification contract.
