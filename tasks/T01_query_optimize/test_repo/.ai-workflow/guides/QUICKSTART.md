# Quick Start — AI-Native Workflow v5.6.35

## 1. Copy the runtime

Copy the complete `.ai-workflow/` directory into the repository root. Do not copy runtime files individually.

## 2. For an existing package, recover state first

```bash
python .ai-workflow/aw_hierarchy.py --root . status
python .ai-workflow/aw_hierarchy.py --root . recover
```

Read:

```text
.ai-workflow/STATE.json
.ai-workflow/docs/PHASE_DIC_EPS_STRUCTURE.md
active Phase/DIC/README.md
active Phase/DIC/REQUESTS.md
active Phase/DIC/PLAN.md
active Phase/reports/REPORT.md
```

## 3. Ordinary new programme

```bash
python .ai-workflow/aw_hierarchy.py --root . init --checkpoint-interval 7
python .ai-workflow/aw_hierarchy.py --root . plan-create "Plan title" "Approved programme goal"
python .ai-workflow/aw_hierarchy.py --root . phase-add "Phase title" "Coherent milestone" --owner Main --accept "observable acceptance condition"
python .ai-workflow/aw_hierarchy.py --root . plan-approve
```

The human approves the Plan. Ordinary Phase progression is machine-managed until a periodic checkpoint or material escalation.

## 4. Build the Phase DIC

Each Phase normally has one DIC package, not many sequential DICs.

```bash
python .ai-workflow/aw_hierarchy.py --root . dic-create <phase-id>
```

Edit the views as appropriate:

- `DIC/README.md` — general summary and reading order;
- `DIC/REQUESTS.md` — specific goals and acceptance requirements;
- `DIC/PLAN.md` — prompt/run graph, dependencies, parallel subagents, merge points and conditional branches;
- `DIC/ARCHITECTURE.md` — only when repository/system architecture changes;
- `DIC/TEST_MATRIX.md` — test/experiment/theory-audit batches when useful.

Add arbitrary custom DIC views when the Phase benefits from them:

```bash
python .ai-workflow/aw_hierarchy.py --root . dic-view-add <phase-id> THEOREM_MAP "<content>" --required
```

Useful custom examples include `EXPERIMENT_PROTOCOL.md`, `DATA_CONTRACT.md`, `GRADER_SPEC.md`, `VENUE_REQUIREMENTS.md`, `NOVELTY_TARGETS.md`, `RELEASE_CONTRACT.md`, and `MIGRATION.md`.

## 5. Generate EPS from the durable plan

The DIC/PLAN may contain 10–100+ stable prompt nodes. EPS instantiates the nodes to run now. Nodes can declare dependencies, `parallel_group`, and `subagent=true`.

```bash
python .ai-workflow/aw_hierarchy.py --root . eps-generate <phase-id> eps_nodes.json
```

Example `eps_nodes.json`:

```json
[
  {"id":"P11A","operation":"derive candidate theorem","parallel_group":"B1","subagent":true},
  {"id":"P11B","operation":"search counterexample","parallel_group":"B1","subagent":true},
  {"id":"P11C","operation":"check nearest literature","parallel_group":"B1","subagent":true},
  {"id":"P12","operation":"reconcile A/B/C","depends_on":["P11A","P11B","P11C"]}
]
```

Ordinary retries or repairs create new EPS/run instances without redefining the DIC unless Phase intent itself changes.

## 6. Optional lanes

The canonical optional lanes are `minor`, `research`, `verification`, and `checkpoints`.

```bash
python .ai-workflow/aw_hierarchy.py --root . lane-set <phase-id> minor off
python .ai-workflow/aw_hierarchy.py --root . lane-set <phase-id> research on
python .ai-workflow/aw_hierarchy.py --root . lane-materialize <phase-id> verification
```

Modes:

```text
off   prohibited
auto  lazy default; create on first use
on    materialize/maintain from the start
```

## 7. Reports are always present

Every Phase has a flat `reports/` directory. Default limit: **10 files**. No `reports/raw/`, `reports/archive/`, or other subfolders.

Base files are:

```text
REPORT.md
RAW_RESULTS.jsonl
MANIFEST.json
```

`RAW_RESULTS.jsonl` is a minimally transformed merged raw surface with provenance. Full forensic evidence can remain under `logs/` and `evidence/`.

## 8. Human check-in pattern

A normal long run looks like:

```text
Human approves Plan
    ↓
Phase 1 … Phase 5–10
    ↓
periodic human checkpoint
    ↓
continue / replan / stop
```

Immediate escalation still occurs for material objective, authority, scientific-claim, frozen-protocol, destructive/external, release/submission, paid-compute, or credential/private-system changes.
