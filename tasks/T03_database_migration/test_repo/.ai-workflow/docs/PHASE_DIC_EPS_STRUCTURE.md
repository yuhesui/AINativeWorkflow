# Phase, DIC, EPS and Reports Structure

This document is the normative file-layout and semantics guide for the v5.6.35 hierarchical runtime.

## 1. Core hierarchy

```text
Goal
└── Plan                         human-scale programme
    └── Phase                    coherent machine milestone
        ├── DIC/                 one durable multi-view contract package
        ├── EPS/                 disposable JIT run instantiations
        ├── actions/             primitive/tool execution records
        ├── logs/                detailed execution logs
        ├── evidence/            phase-local evidence/index material
        ├── reports/             compact canonical output surface: always present
        └── optional lanes/      minor/research/verification/checkpoints
```

The semantic lineage is:

```text
Action <= Prompt/Run <= EPS <= DIC <= Phase <= Plan <= Goal
```

A Phase may involve 10–100+ prompt/runs. **The DIC is not divided into sequential DIC-01/DIC-02 work steps.** There is normally one DIC package for the whole Phase. Its files are complementary views of the same Phase objectives and constraints.

## 2. DIC is a multi-view Phase contract

Canonical layout:

```text
DIC/
├── README.md                    required
├── REQUESTS.md                  required
├── PLAN.md                      required
├── ARCHITECTURE.md              optional / auto
├── TEST_MATRIX.md               optional / auto
├── <CUSTOM_VIEW>.md             user-defined, zero or more
└── MANIFEST.json                machine index; not a second semantic contract
```

### `README.md` — general summary

The orientation view. It explains what the Phase is, why it exists, ownership, boundaries, current state, important inputs, where the DIC views live, and what a fresh session should read first.

It should be concise relative to the rest of the DIC.

### `REQUESTS.md` — specific goals to achieve

The authoritative goal/acceptance inventory for the Phase. Requests describe **what must be resolved**, not the order in which prompts run.

Examples:

- prove or falsify a candidate theorem under explicit assumptions;
- implement a migration while preserving a compatibility contract;
- establish whether C3 improves recovery locality over matched controls;
- compile all three workshop manuscripts under their respective page limits.

Request states may include `OPEN`, `PARTIAL`, `SATISFIED`, `BLOCKED`, `SUPERSEDED`, or `REMOVED`.

Phase completion is determined by request/acceptance resolution and evidence, not by blindly exhausting every planned prompt.

### `PLAN.md` — durable execution plan

`PLAN.md` is explicitly operational. It records the planned prompt graph for the Phase, including:

- prompt/run IDs;
- objective and Request IDs served by each prompt;
- dependencies;
- prompts that may run in parallel;
- subagent delegations;
- model/profile preferences where useful;
- expected outputs and write scopes;
- merge/integration prompts;
- milestone reviews;
- conditional repair, retry, falsification, or independent-review branches.

A useful pattern is:

```text
Batch A
├── P01  inspect/recover state
├── P02A theory derivation         ┐
├── P02B hostile counterexample   ├─ parallel subagents
└── P02C nearest-literature check ┘
        ↓
P03 reconcile P02A/B/C
        ↓
if theorem survives -> P04 independent audit
else                -> P04R obstruction characterization
```

Stable prompt IDs are machine coordination references, **not human approval boundaries**.

### `ARCHITECTURE.md` — target repository/system architecture

Use when the Phase changes repository, runtime, module, schema, CLI, interface, or other system architecture. It should describe current → target architecture, ownership, interfaces, migration/compatibility, invariants, and important failure boundaries.

Do not create it merely to restate general workflow theory.

### `TEST_MATRIX.md` — concrete test/experiment matrix

Use for actual combinations or batches to evaluate. It may describe:

- software test batches;
- algorithms × datasets/tasks × seeds;
- condition × horizon × fault-setting matrices;
- theorem candidate × positive derivation × hostile audit × literature audit;
- manuscript × venue-rule × build/check matrix.

Example:

| Batch | Algorithm | Horizon | Fault | Seeds | Primary measurement |
|---|---|---:|---|---:|---|
| A | C0/C1/C2/C3 | 4 | none | 10 | end-to-end success |
| B | C2/C3 | 12 | injected | 10 | recovery locality |

This is broader than a simple acceptance checklist.

## 3. Custom DIC views

Users may add further flat Markdown views directly to the DIC package. Examples include:

```text
THEOREM_MAP.md
EXPERIMENT_PROTOCOL.md
DATA_CONTRACT.md
BENCHMARK_PROTOCOL.md
GRADER_SPEC.md
CLAIM_POLICY.md
NOVELTY_TARGETS.md
VENUE_REQUIREMENTS.md
PAPER_OUTLINE.md
RELEASE_CONTRACT.md
MIGRATION.md
```

Custom views become first-class DIC components when registered in `DIC/MANIFEST.json`. The runtime command is:

```bash
python .ai-workflow/aw_hierarchy.py dic-view-add <phase-id> THEOREM_MAP "<content>" --required
```

DIC view filenames are flat; do not create another directory hierarchy inside `DIC/`.

## 4. DIC/PLAN versus EPS

The durable plan and EPS intentionally overlap in subject matter but differ in lifetime.

### DIC/PLAN

Persistent execution design:

```text
P11A and P11B run in parallel.
P12 depends on both.
P13 exists only if the theorem survives P12.
```

### EPS

Disposable JIT instantiation for the current repository state, model/context, attempt, and repair history:

```text
EPS attempt 2 for P11A:
- use current Theory profile;
- read these exact authoritative files;
- account for the failed assumption discovered in attempt 1;
- write these outputs;
- stop on these conditions.
```

Ordinary failure/retry should normally create a new EPS/run instance without rewriting the DIC. A DIC changes only when the Phase's actual objectives, constraints, authority, acceptance, or durable execution design materially change.

Canonical EPS layout:

```text
EPS/
├── <eps-id>.json
└── prompts/
    ├── <eps-id>__p11a.md
    ├── <eps-id>__p11b.md
    └── ...
```

An EPS node may specify `depends_on`, `parallel_group`, `subagent`, `plan_node_id`, `model_profile`, expected evidence and local acceptance.

## 5. Optional Phase lanes

The canonical optional lanes are:

```text
minor/
research/
verification/
checkpoints/
```

Each supports:

```text
off   = prohibited for the Phase
auto  = default; not created until first needed
on    = materialize/maintain from Phase initialization
```

Example policy:

```text
minor=auto
research=on
verification=auto
checkpoints=auto
```

This preserves useful execution machinery without making every Phase start with a large empty directory tree.

`reports/` is **not** toggleable; it is always present.

## 6. `reports/` is always present and deliberately small

Every Phase has:

```text
reports/
```

Normative rules:

1. no subdirectories;
2. maximum **10 files by default**;
3. contains human synthesis **and** the key merged raw results;
4. raw result files must remain minimally transformed and provenance-preserving;
5. full forensic evidence may remain in `logs/`, `evidence/`, and optional lanes.

Recommended base surface:

```text
reports/
├── REPORT.md
├── RAW_RESULTS.jsonl
└── MANIFEST.json
```

Additional useful files may include:

```text
RAW_RUNS.jsonl
RAW_GRADER_RESULTS.jsonl
RAW_METRICS.csv
CLAIM_STATUS.json
TEST_RESULTS.csv
BUILD_RESULTS.txt
PROTOCOL.json
ANALYSIS.csv
```

The directory should usually use 3–7 files rather than filling the quota.

### Merged raw semantics

A merged raw file may:

- concatenate source records;
- attach source IDs/paths/hashes;
- normalize encoding;
- normalize a schema or column order losslessly.

It must not silently:

- average or aggregate;
- round values;
- paraphrase raw model results;
- remove failures;
- select favourable cases;
- rewrite the result into a narrative.

Thus:

```text
merged raw = lossless collation + provenance
```

not processed summary.

## 7. Example Phase profiles

### Theory Phase

```text
DIC/
  README.md
  REQUESTS.md
  PLAN.md
  THEOREM_MAP.md
  TEST_MATRIX.md
EPS/
logs/
evidence/
research/          on or auto
verification/      auto
reports/
  REPORT.md
  RAW_RESULTS.jsonl
  CLAIM_STATUS.json
  AUDIT_RESULTS.jsonl
  LITERATURE_MATRIX.csv
  MANIFEST.json
```

### Experiment Phase

```text
DIC/
  README.md
  REQUESTS.md
  PLAN.md
  TEST_MATRIX.md
  EXPERIMENT_PROTOCOL.md
EPS/
logs/
evidence/
research/          auto
verification/      auto
minor/             off after protocol freeze if desired
reports/
  REPORT.md
  RAW_RUNS.jsonl
  RAW_GRADER_RESULTS.jsonl
  RAW_METRICS.csv
  PROTOCOL.json
  MANIFEST.json
```

### Runtime / repository reconstruction Phase

```text
DIC/
  README.md
  REQUESTS.md
  PLAN.md
  ARCHITECTURE.md
  TEST_MATRIX.md
EPS/
actions/
logs/
evidence/
minor/             auto
verification/      auto
reports/
  REPORT.md
  RAW_RESULTS.jsonl
  TEST_RESULTS.csv
  BUILD_RESULTS.txt
  MANIFEST.json
```

## 8. Governance scale

The richer Phase structure does **not** reintroduce per-prompt human approval.

```text
Human governance:
Plan approval -> periodic review roughly every 5–10 Phases -> material escalation

Machine execution:
Phase -> DIC views -> PLAN prompt graph -> EPS instances -> prompt/runs -> actions
```

Local checking should happen continuously. Lightweight milestone rechecks may happen after prompt clusters or at DIC closure. Fresh independent review is reserved for material scientific evidence, frozen experiments, release boundaries and submission manuscripts.

## 9. Compatibility

The older `phases/phase_XX/` Goal/Structured CLI remains a compatibility surface. New long-horizon research work should use `.ai-workflow/runtime/plans/...` as the canonical hierarchy. Compatibility mode must not become a competing source of Plan/Phase authority.
