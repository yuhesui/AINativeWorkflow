# NeurIPS 2026 Education Track — Full Slide Plan

## Working title

# AI Native Workflow for Research
## Formalizing the AI workflows researchers already use

**Presenter:** Yuhe Sui  
**Affiliation:** Quantitative Research Society @ NTU  
**Prepared duration:** 18–20 minutes  
**Short cut:** approximately 14–15 minutes by removing the marked optional slides  
**Primary source:** `technical_report/AI_NATIVE_WORKFLOW_TECHNICAL_REPORT.tex/.pdf`  
**Operational source:** `.ai-workflow/guides/DETAILED_WORKFLOW_GUIDE.md`

---

# 0. Visual system inherited from the current deck

The Education deck should look like a simplified, lighter continuation of the current `AI Native Workflow` presentation rather than a new visual identity.

## Page anatomy

Every ordinary content slide should use the same hierarchy:

1. **top-left section line** — e.g. `I · FROM INFORMAL TO FORMAL AI RESEARCH WORKFLOWS`;
2. **main title** — one line where possible;
3. **thin red rule** directly below the main title;
4. **subtitle / teaching proposition** — one short sentence;
5. **main visual/body** — normally one diagram, one comparison, or one worked example rather than many small cards;
6. **source line** — compact `Technical Report §§...` or `Detailed Guide §...` reference;
7. **footer** — `AI Native Workflow 5.6` at lower left and slide number at lower right.

## Typography and visual treatment

- Use **Frutiger 45 Light** throughout; no bold face.
- Background should be predominantly pure white.
- Use very light beige / warm gold fills for secondary containers; avoid large dark-grey panels.
- Preserve the current human/machine visual distinction:
  - **human-facing / researcher-facing:** blue;
  - **machine / AI-facing:** red.
- Use grey only for low-salience supporting text, arrows, or inactive branches.
- Arrows must be large enough to read at presentation distance.
- Avoid brightly colored graph nodes; use white/beige cards with blue/red labels or borders instead.
- Keep diagrams flat and left-to-right or top-to-bottom; avoid decorative 3-D agent graphics.

## Teaching principle

Introduce the **human research experience first**, then name the formal workflow object. Terms such as DIC and EPS should appear only after the audience already understands the problem they solve.

A recurring example runs through the talk:

> A researcher is developing a new ML method for a workshop paper. They already use ChatGPT for planning/interpretation, a research surface for literature, and Codex or Claude Code for implementation and experiments.

---

# Section I · From informal to formal AI research workflows

## Slide 1 — AI Native Workflow for Research

### Section line
`I · FROM INFORMAL TO FORMAL AI RESEARCH WORKFLOWS`

### Main title
**AI Native Workflow for Research**

### Subtitle
**Formalizing the AI workflows researchers already use so current systems can carry more coordination without consuming proportionally more researcher attention.**

### Presenter block
Bottom-left of the main canvas, above the footer:

```text
Yuhe Sui
Quantitative Research Society @ NTU
```

### Main visual
Use the current deck’s clean title-page language, but replace the previous role questions with three Education-facing questions arranged vertically on the right:

```text
How much of a research project can current AI systems coordinate?

How do we keep a long AI research programme centred on one scientific aim?

Where should researcher attention remain final?
```

On the left, a thin vertical progression:

```text
AI assistance
      ↓
AI workflow
      ↓
long-horizon AI execution
```

The final phrase is visually larger than the first two.

### Speaker message
Most researchers do not start from zero. They already have a practical workflow across chat, research, and coding tools. This presentation is about **formalizing and improving that workflow**, not replacing it with a completely different system.

### Source
`Technical Report §§1.1–1.5, 20.1–20.3`

### Time
**0:45**

---

## Slide 2 — You probably already have an AI workflow

### Section line
`I · FROM INFORMAL TO FORMAL AI RESEARCH WORKFLOWS`

### Main title
**You probably already have an AI workflow**

### Subtitle
The workflow exists; the important question is where its state, coordination, and acceptance logic live.

### Layout
Use a **full-width horizontal pipeline**, similar to the current deck’s operating-flow slides:

```text
Persistent Chat
planning / theory / interpretation
        ↓
Research Surface
literature / novelty / external evidence
        ↓
Codex / Claude Code
implementation / experiments
        ↓
Persistent Chat
analysis / paper / next decision
```

Under the pipeline, place one long blue researcher bar:

```text
RESEARCHER CURRENTLY CARRIES:
what was decided · which result is current · what each agent knows · what should run next · what is actually accepted
```

### Human example
On the lower right, a tiny transcript-style callout:

```text
Researcher: “Continue from yesterday’s experiment plan.”
AI: “Can you remind me what we decided?”
```

Do not make this comedic; it is simply a recognizable operating failure.

### Key line
**The informal workflow is already hierarchical — but much of the hierarchy still lives in the researcher’s attention.**

### Source
`Technical Report §§1.1–1.3, 7.1–7.2`

### Time
**1:05**

---

## Slide 3 — The hidden bottleneck is researcher attention

### Section line
`I · FROM INFORMAL TO FORMAL AI RESEARCH WORKFLOWS`

### Main title
**AI execution can scale faster than supervisory attention**

### Subtitle
The target is not simply lower wall-clock time; it is lower human attention required per unit of verified research progress.

### Layout
Use a **two-column before/after composition**.

#### Left — today’s informal workflow
Place a blue researcher silhouette/box in the middle. Around it, six small white callouts:

- remember the accepted objective;
- copy context between tools;
- decide which branch is stale;
- reconcile conflicting outputs;
- check what actually ran;
- reconstruct failures and next actions.

A red ring around the researcher should be labeled **routine coordination attention**.

#### Right — desired allocation
Use two stacked boxes:

**MACHINE-MANAGED** in red:

```text
routing · prompt sequencing · state · local retries · evidence indexing · handoff
```

**HUMAN-VALUED** in blue:

```text
scientific objective · surprising evidence · material method changes · claims · release/submission
```

At the bottom, show the metric only as an intuition, not a proof claim:

```text
human-attention intensity
≈ supervisory attention / verified research progress
```

### Key line
**Reduce coordination attention; preserve scientific attention.**

### Source
`Technical Report §§1.2, 4.11, 6.12–6.13, 14.1`

### Time
**1:10**

---

## Slide 4 — Two ways long AI research loses its scientific centre

### Section line
`I · FROM INFORMAL TO FORMAL AI RESEARCH WORKFLOWS`

### Main title
**Every local response can look reasonable while the programme drifts**

### Subtitle
Two recurring workflow failures are constraint–objective inversion and salience flattening.

### Layout
Two equal columns with simple trajectories.

#### Left — constraint–objective inversion / defensive drift

```text
Primary Aim
“find the strongest correct result”
        ↓
reviewer-style critique
        ↓
more critique
        ↓
more defensive repair
        ↓
Drifted effective objective
“make the work impossible to criticize”
```

Use blue for the original Primary Aim and progressively more grey/red toward the drifted endpoint.

Under it:

> “Avoid unsupported claims” is a constraint, not the scientific objective.

#### Right — salience flattening

Show two miniature research portfolios.

**Clear centre of gravity:**

```text
MAIN RESULT          ███████████
supporting theorem   ████
control              ███
limitation           ██
optional extension   ░
```

**Flattened programme:**

```text
idea A       █████
idea B       █████
idea C       █████
control      █████
extension    █████
```

### Human example
“After several AI sessions, the paper has five interesting directions and no longer has one obvious sentence describing what it is trying to establish.”

### Key line
**Constraints should bound ambition; they should not replace it. Supporting branches should strengthen one Primary Aim, not compete equally for attention.**

### Source
`Technical Report §§1.4, 4.8, 6.10–6.11, 20.4`

### Optional cut
**Yes.** Remove for a shorter talk; mention both patterns verbally on Slide 3.

### Time
**1:05**

---

## Slide 5 — What must survive outside the conversation?

### Section line
`I · FROM INFORMAL TO FORMAL AI RESEARCH WORKFLOWS`

### Main title
**A research project needs durable state, not just a longer context window**

### Subtitle
Five things must remain inspectable even when every AI session is replaced.

### Layout
Five wide horizontal cards, not five small icons:

```text
INTENT      What are we actually trying to establish?
AUTHORITY   What may AI decide or change without returning to the researcher?
STATE       What is the current project truth?
EVIDENCE    What actually ran, failed, or was proved?
ACCEPTANCE  What would be sufficient to call this Phase complete?
```

Under the cards place one simple recovery test:

```text
Fresh chat tomorrow + repository only
              ↓
Can the project be reconstructed correctly?
```

### Speaker message
This is the transition from a collection of AI conversations to a project operating system.

### Source
`Technical Report §§1.3, 4.2–4.4, 13.1–13.3`

### Time
**0:55**

---

# Section II · AI Native Workflow as a formalized research operating model

## Slide 6 — Formalize the workflow you already use

### Section line
`II · AI NATIVE WORKFLOW AS A RESEARCH OPERATING MODEL`

### Main title
**AI Native Workflow externalizes the coordination layer**

### Subtitle
The researcher keeps scientific authority; different AI surfaces take responsibility for planning, evidence acquisition, execution, and checking.

### Layout
Use the current deck’s **human-facing blue / machine-facing red** architecture diagram.

```text
                         HUMAN RESEARCHER
                                │
                                ▼
                              MAIN
                 Primary Aim · Phase planning · decisions
                                │
              ┌─────────────────┼─────────────────┐
              ▼                 ▼                 ▼
           RESEARCH          THEORY          EXPERIMENT
           evidence          reasoning        protocol
              └─────────────────┼─────────────────┘
                                ▼
                       DIC + INITIAL EPS
                         Main-authored
                                │
                                ▼
                    CODING-AGENT ORCHESTRATOR
                  validate · tune · schedule · integrate
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
             Worker A        Worker B        Worker C
                └───────────────┼───────────────┘
                                ▼
                    EVIDENCE / VERIFICATION
                                │
                                ▼
                       MAIN / RESEARCHER
```

Blue: Human, Main, scientific judgement.  
Red: Orchestrator, Workers, tool execution.  
Research/Theory/Experiment should use light neutral cards with blue headings because they inform scientific decisions rather than directly own repository mutation.

### Key line
**Main is the semantic centre; the coding Orchestrator is the operational centre.**

### Source
`Technical Report §§4.5–4.7, 5.8–5.10, 6.1–6.3`

### Time
**1:20**

---

## Slide 7 — Why this is practical with current AI settings

### Section line
`II · AI NATIVE WORKFLOW AS A RESEARCH OPERATING MODEL`

### Main title
**No new foundation model is required**

### Subtitle
The workflow composes capabilities already available in current chat, research, coding-agent, and repository environments.

### Layout
Use a **left-to-right mapping table**, similar to the current deck’s “agent surfaces” slide.

| Current surface | Natural workflow responsibility |
|---|---|
| Persistent ChatGPT / Claude | Main: objective, planning, synthesis, material decisions |
| Deep Research / browsing | external literature, novelty, source comparison |
| specialist reasoning chat | Theory or Experiment design when useful |
| Codex / Claude Code | repository-aware Orchestrator execution |
| coding-agent subagents | bounded independent work / parallel inspection |
| files + manifests + repository | durable project state |
| tests / analysis scripts / renderers | machine-checkable evidence |

At bottom:

> **Hierarchical planning becomes usable because the hierarchy can be mapped onto surfaces researchers already have.**

### Source
`Technical Report §§2.3, 3, 4.3, 7.2`

### Optional cut
**Yes.** If time is short, compress into one spoken sentence on Slide 6.

### Time
**0:55**

---

## Slide 8 — Plan hierarchically instead of writing one enormous prompt

### Section line
`II · AI NATIVE WORKFLOW AS A RESEARCH OPERATING MODEL`

### Main title
**Different timescales need different objects**

### Subtitle
The stable scientific programme is refined progressively until it becomes bounded executable work.

### Layout
Use a large centered vertical hierarchy with each level occupying progressively less width:

```text
GOAL
What is the overall research destination?

PLAN
What major milestones make the programme credible?

PHASE
What coherent milestone should be completed now?

DIC
What must remain true while this Phase is executed?

EPS
What prompt/dependency graph will execute this Phase?

PROMPT / RUN
What bounded executor task runs now?

ACTION
What tool call, edit, test, search, or experiment happens next?
```

Human-facing layers `GOAL → PLAN → PHASE → DIC → initial EPS` have a blue spine.  
Below the initial EPS, the execution spine transitions to red.

### Clarify ownership directly on the slide

```text
MAIN AUTHORS:     Goal/Plan/Phase interpretation · DIC · initial EPS/prompt graph
ORCHESTRATOR:     validate · model-tune · schedule · execute · integrate · bounded repair EPS
```

### Key line
**Hierarchy protects scientific meaning while allowing execution details to adapt.**

### Source
`Technical Report §§4.3, 5.2–5.8, 9.1–9.4`

### Time
**1:10**

---

## Slide 9 — What Main actually hands to the coding agent

### Section line
`II · AI NATIVE WORKFLOW AS A RESEARCH OPERATING MODEL`

### Main title
**One Phase becomes one self-contained, inspectable package**

### Subtitle
Project-specific Phase state lives at repository root under `phases/`, not hidden inside the reusable runtime.

### Layout
Use a **large file-tree visual on the left (60%)** and explanation on the right (40%).

```text
phases/
└── phase_05_method_validation/
    ├── DIC/
    │   ├── README.md
    │   ├── REQUESTS.md
    │   └── PLAN.md
    ├── EPS/
    │   └── eps_001/
    │       ├── manifest.json
    │       └── prompts/
    ├── ORCHESTRATOR_START.md
    ├── reports/
    ├── results/
    ├── evidence/
    ├── artifacts/
    └── logs/
```

Right column:

```text
.ai-workflow/
reusable operating system

phases/
project-specific research history
```

Then show the import path in one line:

```text
Main Phase ZIP → aw phase import MAIN_PHASE.zip → ready repository Phase
```

### Speaker message
The important point is not the filenames themselves. It is that a fresh Main, researcher, or coding agent can find the current contract, prompts, summary, structured results, and raw evidence without reverse engineering a chat transcript.

### Source
`Technical Report §7 “Operational Use”; Detailed Guide: PHASE_FILESYSTEM.md`

### Optional cut
**Yes**, if the final slot is very short. Keep it in the downloadable teaching deck even if not presented live.

### Time
**1:00**

---

# Section III · DIC, EPS, and autonomous execution

## Slide 10 — DIC: keep a complicated AI project intelligible

### Section line
`III · DIC, EPS, AND AUTONOMOUS EXECUTION`

### Main title
**Machine execution may expand; the researcher’s control surface should not**

### Subtitle
The DIC is both a durable machine contract and a human-intelligibility projection.

### Layout
Use a **three-stage compression diagram**.

#### Left — machine complexity
A dense but tidy list:

```text
12 prompts
5 subagents
4 research reports
3 failed experiments
2 repair attempts
hundreds of tool actions
```

Arrow into centre.

#### Centre — DIC Core 3
Three stacked large cards:

```text
README.md
Primary Aim · orientation · authority

REQUESTS.md
prioritized outcomes · acceptance

PLAN.md
sequence · dependencies · parallelism · merge / repair graph
```

Arrow into right.

#### Right — researcher asks only

```text
What are we trying to establish?
What evidence matters?
What remains unresolved?
What decision needs me?
```

### Primary Aim callout
A blue strip at the top:

> **PRIMARY AIM: the one result this Phase exists to establish.**

### Key line
**As machine execution becomes more complex, the human interface should become more compact — not less intelligible.**

### Source
`Technical Report §§4.4, 5.4–5.5, 6.9–6.11, 13.3`

### Time
**1:15**

---

## Slide 11 — EPS: make the Phase plan executable

### Section line
`III · DIC, EPS, AND AUTONOMOUS EXECUTION`

### Main title
**Main commits the prompt graph; the Orchestrator compiles and runs it**

### Subtitle
DIC/PLAN.md is the durable semantic graph. The initial EPS is Main’s concrete bounded prompt graph for the first execution attempt.

### Layout
Two large side-by-side diagrams with a clear arrow between them.

#### Left — durable DIC/PLAN graph

```text
A · inspect evidence
      ↓
 ┌────┴────┐
 ↓         ↓
B · theory C · experiment
 └────┬────┘
      ↓
D · reconcile
      ↓
E · verify
```

Label below:

```text
stable meaning
Primary Aim / dependencies / evidence gates
```

#### Right — initial EPS

```text
P01  inspect repository + evidence
      ↓
 ┌────┴────┐
 ↓         ↓
P02A       P02B
Theory     Experiment
prompt     prompt
 └────┬────┘
      ↓
P03  integrate outputs
      ↓
P04  verification package
```

Label:

```text
Main-authored first executable realization
```

Below both, a red Orchestrator strip:

```text
ORCHESTRATOR:
validate → compile wording for actual model/surface → schedule → execute → integrate
```

Then a small repair branch:

```text
execution-local defect → repair EPS_002
material scientific change → return to Main / DIC replan
```

### Key line
**Main chooses what the prompt graph means; Orchestrator chooses how to execute it well on the actual coding-agent surface.**

### Source
`Technical Report §§5.6–5.8, 6.5–6.7, 9.4; Detailed Guide §§4.5, 12–13`

### Time
**1:20**

---

## Slide 12 — Parallelism without fragmentation

### Section line
`III · DIC, EPS, AND AUTONOMOUS EXECUTION`

### Main title
**Parallel branches are useful only when their interfaces are explicit**

### Subtitle
The prompt graph lets independent scientific work proceed concurrently while preserving one integration point and one Primary Aim.

### Layout
Use a simple research question at the top:

> **Is the proposed method genuinely new, theoretically meaningful, and empirically useful?**

Below it:

```text
                    Main-authored EPS
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
 Literature /         Theory /         Experiment /
 novelty              counterexample   matched controls
 report                report           results
          └───────────────┼───────────────┘
                          ▼
                   MAIN RECONCILIATION
                          ▼
                   next Phase decision
```

Use a small side panel:

**Safe to parallelize when**

- evidence is independent;
- writes are disjoint or read-only;
- dependencies are declared;
- a merge node exists.

**Do not parallelize**

- multiple agents silently editing the same canonical paper or protocol;
- branches that depend on unresolved upstream evidence.

### Key line
**Parallelism creates value because ownership, dependencies, evidence, and integration order are explicit.**

This preserves one of the clearest lines from the existing deck.

### Source
`Technical Report §§4.7, 5.9–5.10, 6.8, 7 parallelism/integration subsections`

### Time
**1:05**

---

## Slide 13 — A research route can change without losing the objective

### Section line
`III · DIC, EPS, AND AUTONOMOUS EXECUTION`

### Main title
**Real research rarely follows the first route**

### Subtitle
The workflow should preserve negative evidence and adapt execution without rewriting history as success.

### Layout
Use a horizontal **five-day timeline**.

```text
DAY 1
literature + baseline qualification

DAY 2
method implementation + theory attack

DAY 3
primary experiment fails gate

DAY 4
bounded alternative route + new EPS

DAY 5
statistical verification + narrower supported claim
```

At Day 3 use a visible red failure marker. Under Day 3–5 show:

```text
failed branch preserved
        ↓
route changes
        ↓
Primary Aim / evidence standard remains visible
```

### Human example text
Use a generic research story in the main deck; in speaker notes mention that the current workflow package contains real project examples where negative comparisons were retained and the final claim boundary was narrowed instead of narrating all branches as success.

### Key line
**The workflow is designed to preserve scientific ambition and negative evidence at the same time.**

### Source
`Technical Report §§7.8, 20.4–20.5; current presentation’s HealthFormer-RL worked example can be reused as supporting material.`

### Optional cut
**Yes.** The generic example can be removed without damaging the architecture explanation.

### Time
**1:05**

---

## Slide 14 — The Orchestrator handles execution mechanics, not scientific meaning

### Section line
`III · DIC, EPS, AND AUTONOMOUS EXECUTION`

### Main title
**The researcher should design the research — not schedule every AI turn**

### Subtitle
Once the Phase package is accepted, routine execution lives below the human-attention boundary.

### Layout
Two columns.

#### Left — manual informal workflow

```text
open coding agent
paste task A
wait
open second agent
paste task B
copy B back to A
notice file conflict
re-explain the experiment
ask what ran
repair the state
```

Cross this with a thin grey line; do not use a large red “X”.

#### Right — formalized execution

```text
Main Phase ZIP
      ↓
aw phase import
      ↓
Orchestrator readiness
      ↓
model-tuned prompts
      ↓
parallel bounded Workers
      ↓
integration + evidence
      ↓
compact return / exception
```

Below:

> The Orchestrator may repair execution-local defects. It may not silently alter the Primary Aim, frozen method, acceptance criteria, or claim boundary.

### Source
`Technical Report §§5.8–5.12, 6.2, 7 operational protocol; Detailed Guide §12`

### Time
**0:55**

---

# Section IV · Evidence, recovery, and human authority

## Slide 15 — Reports should save attention without hiding evidence

### Section line
`IV · EVIDENCE, RECOVERY, AND HUMAN AUTHORITY`

### Main title
**Human-readable conclusions and machine-readable results should coexist**

### Subtitle
A report is an index into evidence, not a replacement for it.

### Layout
Three vertical layers.

#### Top — human-facing reports, blue

```text
reports/PHASE_SUMMARY.md
What is currently true?

reports/FINAL_HANDOFF.md
What was established, not established, and what should happen next?
```

#### Middle — structured results, beige

```text
results/KEY_RESULTS.json
required when key results are naturally structured

results/KEY_RESULTS.csv
when tabular representation is appropriate
```

#### Bottom — raw provenance, red/grey

```text
evidence/EVIDENCE_MANIFEST.json
artifacts/
logs/
```

Arrow from bottom to top labeled **compression without evidence loss**.

### Human example
The researcher should not have to read 600 terminal lines to learn that one frozen seed failed and therefore a table is incomplete. The summary states that fact; the exact logs remain addressable.

### Key line
**Concise human reports are valuable only when the raw evidence remains recoverable.**

### Source
`Technical Report §§6.14, 13.3, 20.2; Detailed Guide PHASE_FILESYSTEM.md`

### Time
**1:05**

---

## Slide 16 — Verification should change what executes next

### Section line
`IV · EVIDENCE, RECOVERY, AND HUMAN AUTHORITY`

### Main title
**A failed check is an execution-control signal, not just a score**

### Subtitle
When an upstream result changes, only declared dependent work should need reconsideration.

### Layout
Reuse/adapt the strongest Who Verifies dependency-cone visual.

```text
collect        normalize
                  │
                  ▼
              experiment
                  │
                  ▼
                table
                  │
                  ▼
                paper
                  │
                  ▼
               release

independent theory
```

When `normalize` fails:

- affected cone `experiment → table → paper → release` highlighted red;
- `collect` and `independent theory` remain blue/neutral;
- arrow to `repair EPS_002`;
- final `accept` gate.

At bottom show the four outcomes:

```text
ACCEPT     REPAIR     REPLAN     ESCALATE
```

### Key line
**Local repair is efficient only when the dependency declarations are trustworthy.**

### Source
`Technical Report §§5.11–5.12, 11–12, 17; Who Verifies deterministic demonstration.`

### Time
**1:10**

---

## Slide 17 — Human authority becomes exception-driven

### Section line
`IV · EVIDENCE, RECOVERY, AND HUMAN AUTHORITY`

### Main title
**Remove the researcher from routine coordination — not from scientific authority**

### Subtitle
Autonomy is useful when routine continuation is machine-managed and consequential semantic changes return upward.

### Layout
Use a **two-column authority table**, based directly on the current deck’s “bounded autonomy and human authority” slide.

#### AI may manage inside the accepted Phase

- repository inspection;
- model-tuned prompt compilation;
- bounded subagent routing;
- ordinary experiment execution;
- local tests and repairs;
- evidence indexing;
- integration and compact handoff;
- repair EPS under unchanged DIC.

#### Researcher / Main remains final for

- the Primary Aim and meaning of success;
- material changes to method or estimand;
- new public scientific claims;
- destructive / external / paid / permission-expanding actions;
- release and submission;
- whether the workflow’s complexity is justified.

### Human example
A coding agent discovers that switching the evaluation metric makes the method look much better. That is **not** an implementation repair. It changes the scientific question and must return to Main/researcher.

### Key line
**Human attention should be spent where a decision changes scientific meaning or external responsibility.**

### Source
`Technical Report §§6.12–6.13, 7.18, 14, 20.2–20.3`

### Time
**1:00**

---

## Slide 18 — What we claim — and what still needs evaluation

### Section line
`IV · EVIDENCE, RECOVERY, AND HUMAN AUTHORITY`

### Main title
**The architecture is implemented; the efficiency hypothesis still needs measurement**

### Subtitle
Do not turn design objectives into empirical claims before the comparison is run.

### Layout
Two large columns.

#### Established / implemented

- durable Goal → Plan → Phase → DIC → EPS hierarchy;
- one multi-view DIC per Phase;
- Main-authored initial EPS and bounded repair EPS lineage;
- evidence-linked Actions;
- `accept / repair / replan / escalate` transitions;
- package-only recovery;
- deterministic dependency-local repair demonstration;
- current runtime conformance tests.

#### Evaluation targets

- lower human attention per unit of verified progress;
- lower intervention frequency;
- lower manual context-transfer burden;
- stronger long-horizon claim/evidence fidelity;
- better recovery efficiency than flat workflows;
- conditions under which hierarchy is worth its overhead.

### Key line
**The framework is a testable operating hypothesis, not a claim that hierarchy always improves research.**

### Source
`Technical Report §§18–21`

### Optional cut
**Yes.** For a live Education talk, this can be compressed into the closing; keep it in the downloadable deck for scientific integrity.

### Time
**0:55**

---

# Section V · Adapt the workflow to your own research

## Slide 19 — You can adopt the whole workflow or only the parts you need

### Section line
`V · ADAPT THE WORKFLOW TO YOUR OWN RESEARCH`

### Main title
**AI Native Workflow is a reference architecture, not a required ritual**

### Subtitle
Researchers can install the complete runtime, adapt the structure, or borrow individual controls to strengthen an existing workflow.

### Layout
Use **three increasing adoption levels**, left to right.

#### Level 1 — borrow the ideas

```text
Primary Aim
Phase summaries
explicit evidence
human gates
```

Caption: keep your existing ChatGPT → Codex workflow.

#### Level 2 — formalize the handoff

```text
DIC Core 3
Main-authored EPS
Phase folder
reports/results/evidence
```

Caption: add durable project state and prompt/dependency graphs.

#### Level 3 — install the full runtime

```text
.ai-workflow/
aw phase import
Orchestrator protocol
repair/recovery lineage
verification
```

Caption: use the complete reference implementation.

At bottom:

> **Adoption path: enhance what already works rather than replacing every research habit at once.**

### Source
`Technical Report §§7.1–7.2, 20.1, 20.7; QUICKSTART.md`

### Time
**1:05**

---

## Slide 20 — Closing: spend researcher attention on the science

### Section line
`V · ADAPT THE WORKFLOW TO YOUR OWN RESEARCH`

### Main title
**The goal is useful autonomy, not autonomy for its own sake**

### Subtitle
Formalize enough of the workflow that AI can coordinate more of the routine work while the researcher retains the scientific centre.

### Layout
Use a clean closing page with three takeaways, similar to the current deck’s numbered summary cards but much less dense.

```text
01
FORMALIZE WHAT ALREADY EXISTS
Chat + research + coding agents become one durable workflow.

02
MAKE HIERARCHY HUMAN-INTELLIGIBLE
Primary Aim → Phase → DIC → EPS preserves one centre of gravity while execution scales.

03
REDUCE COORDINATION ATTENTION
Let machines manage routine routing, evidence, and recovery; reserve human attention for scientific judgement.
```

Large closing line across the bottom:

> **Reduce coordination attention. Preserve scientific attention.**

Presenter block beneath:

```text
Yuhe Sui
Quantitative Research Society @ NTU
```

Optional final small line:

```text
AI Native Workflow 5.6 · Technical Report · Quick Start · .ai-workflow/
```

### Source
`Technical Report §§20–22`

### Time
**0:45**

---

# Timing and cut plan

## Full prepared version

| Section | Slides | Target time |
|---|---:|---:|
| I · From informal to formal AI research workflows | 1–5 | ~5:00 |
| II · AI Native Workflow as a research operating model | 6–9 | ~4:25 |
| III · DIC, EPS, and autonomous execution | 10–14 | ~5:30 |
| IV · Evidence, recovery, and human authority | 15–18 | ~4:10 |
| V · Adapt the workflow to your own research | 19–20 | ~1:50 |
| **Total prepared** | **20** | **~20:55 maximum; rehearse to ~18–19 min** |

The scripted wording should be tighter than the maximum page timings above. The visual deck deliberately contains removable material so the final allocated Education slot can be accommodated without redesign.

## ~15-minute cut

Remove:

- **Slide 4** — two semantic drifts; mention verbally on Slide 3;
- **Slide 7** — current AI surfaces; fold the point into Slide 6;
- **Slide 9** — detailed filesystem/import view; keep in downloadable materials;
- **Slide 13** — multi-day route example;
- **Slide 18** — evidence-status slide; fold the non-claim into Slide 20.

This leaves **15 slides** and preserves the complete conceptual arc.

## ~10–12-minute emergency cut

Additionally remove:

- Slide 5;
- Slide 14;
- Slide 15.

Keep Slides 1–3, 6, 8, 10–12, 16–17, 19–20.

---

# Speaker-note principles

1. **Do not read architecture labels one by one.** Explain the human problem, then point to the layer that absorbs it.
2. **Do not oversell productivity.** Say `human attention per unit of verified progress`, not “the workflow saves time.”
3. **Keep defensive drift and salience flattening explicitly framed as workflow observations/failure patterns**, not universal empirical claims about every LLM.
4. **Keep hierarchy subordinate to the workflow concept.** The lesson is AI Native Workflow for Research; hierarchy is the mechanism that makes the workflow durable and executable.
5. **Use DIC as the main human-intelligibility idea.** A DIC exists partly so machine output does not become progressively less intelligible and therefore more expensive for a researcher to supervise.
6. **Use EPS ownership precisely:** Main authors the initial prompt graph; Orchestrator compiles/tunes/executes it and may issue bounded repair EPS revisions under the unchanged DIC.
7. **Keep evidence status honest.** The architecture, runtime, conformance checks, and deterministic repair demo are implemented; comparative human-attention benefits remain evaluation targets.
8. **End on adaptation.** The audience should leave thinking “I can improve my existing workflow tomorrow,” not “I need to adopt an entire new agent platform.”
