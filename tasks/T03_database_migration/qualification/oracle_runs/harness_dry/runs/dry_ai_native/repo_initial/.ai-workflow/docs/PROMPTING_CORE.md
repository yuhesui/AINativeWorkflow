# PROMPTING_CORE.md — Normative Prompting Standard

## 1. Universal prompt anatomy

Every nontrivial prompt should contain:

```text
role and authority
managed workflow context
repository root
preserved rough input
bounded interpretation
objective and request mapping
dependencies/readiness evidence
read-first files
allowed paths/actions
forbidden paths/actions
backend and evidence target
ordered work packages
required outputs/schemas
risk-adaptive checks
logging/evidence
recoverable repair policy
critical stop conditions
return contract
```

Repeat load-bearing constraints even when the phase README also contains them. Do not force a Worker
to infer path authority, evidence level or approval from unrelated files.

## 2. Outcome-first and file-aware

State one observable outcome. Name exact files or file families. Required outputs must fall inside
allowed paths. If the prompt needs source/test/log paths outside authority, repair the contract
before execution.

Preserve the user's exact rough wording separately from interpretation. Distinguish requirement,
preference, example and strategy.

## 3. Config-managed context

Templates include `{{WORKFLOW_CONTEXT}}`, rendered from config/package/phase metadata. After
changing mode, repository root, levels, routing profile, available models or surfaces, run:

```bash
aw update
aw validate
```

Do not manually edit the managed block. Terminal prompts are skipped by default to preserve
historical evidence.

## 4. GPT-5.6 prompt strategy

- Sol: complex synthesis/architecture and persistent Main work with precise constraints, source
  hierarchy, explicit authority, and the highest exposed reasoning setting when required.
- Terra: bounded multi-file implementation with deterministic outputs and checks.
- Luna: mechanical, file-local work with narrow authority and clear validation.

Current OpenAI guidance favors concise, clearly delimited objectives and explicit autonomy,
approval, and evidence requirements. Avoid redundant restatement once constraints are unambiguous.

Ask for evidence, conclusions and decision records—not hidden chain of thought. Give examples only
when they reduce ambiguity; label them as examples.

## 5. Claude/Codex/Copilot execution prompts

CLI agents need complete operational detail:

- repository and current phase;
- exact read-first list;
- edit boundaries;
- commands and test profile;
- permission limits;
- log path;
- what to return to Orchestrator.

For Claude Opus 5 and Sonnet 5, use clear direct instructions, durable repository state, and
adaptive thinking where the product exposes it. Do not pass legacy manual thinking-token budgets
to Sonnet 5. Avoid unnecessary over-verification instructions; define the acceptance evidence once.

Do not write “inspect and fix everything.” Do not rely on chat memory. A fresh agent should be able
to execute from files alone.

## 6. Backend/evidence language

Use explicit statements:

```yaml
backend_kind: real
evidence_target: pilot
```

The prompt must say what weaker backends are forbidden. State that smoke, qualification and pilot
are different. Require actual checkpoint loading when evaluating a learned policy.

## 7. Checks and gates

Worker prompts name checks, not formal gate passage. Verifier prompts define acceptance gates and
independent recomputation. Do not burden every Worker with a full verification framework.

Use risk-adaptive tests. Specify affected interfaces and when full tests are required.

## 8. Recovery and stopping

Recoverable defects should be repaired and rerun. Critical stop conditions should be few and
material: authority, rollback, invalid evidence, data/security, material science/architecture,
external/paid/release action.

Avoid contradictory instructions such as “do not stop” and “stop on any test failure.”

## 9. Prompt anti-patterns

- output outside allowed path;
- exact method hidden in prose rather than config;
- proxy backend described as real;
- planning ceiling represented as measured feasibility;
- no failure retention;
- no dependency evidence;
- brittle gate requiring already-feasible residual to improve indefinitely;
- architecture/model expansion without diagnostic justification;
- huge Cartesian search;
- repeated user GO requests;
- Orchestrator self-verifying formal acceptance.
