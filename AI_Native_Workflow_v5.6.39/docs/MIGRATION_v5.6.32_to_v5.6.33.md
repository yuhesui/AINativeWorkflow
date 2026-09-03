# Migration — v5.6.32 to v5.6.33

v5.6.33 keeps the v5.6.32 Plan-level governance model but expands the internal Phase representation.

## Structural mapping

```text
v5.6.32
<phase>/
  DIC.json
  eps/*.json
  actions/*.json

v5.6.33
<phase>/
  DIC/
    README.md
    REQUESTS.md
    PLAN.md
    ARCHITECTURE.md?
    TEST_MATRIX.md?
    <CUSTOM>.md?
    MANIFEST.json
  EPS/
    <eps>.json
    prompts/
  actions/
  logs/
  evidence/
  reports/
    REPORT.md
    RAW_RESULTS.jsonl
    MANIFEST.json
  minor|research|verification|checkpoints/   # off|auto|on
```

The migration preserves each existing DIC ID, EPS ID, Action record and scientific evidence pointer. Historical v5.6.32 EPS records were coarse; their new `DIC/PLAN.md` views therefore reconstruct only the execution detail that was actually recorded and explicitly state that no unrecorded prompts were invented.

The canonical state schema advances to 5.6.33 and records default lane/view/report policy. Existing project outputs remain in their natural repository locations rather than being duplicated into the Phase folder.
