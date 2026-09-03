# PHASE_FILESYSTEM.md - Default Project-Local Phase Surface

Each Phase lives at repository root `phases/<phase_id>/`. `.ai-workflow/` is the reusable runtime; `phases/` is project-specific research/work state.

```text
phases/<phase_id>/
├── DIC/
│   ├── README.md
│   ├── REQUESTS.md
│   └── PLAN.md
├── EPS/
│   └── <eps_id>/
│       ├── manifest.json
│       └── prompts/
├── ORCHESTRATOR_START.md
├── reports/
│   ├── PHASE_SUMMARY.md
│   ├── VERIFICATION_001.md        # when formal verification occurs
│   └── FINAL_HANDOFF.md           # required at terminal handoff
├── results/
│   ├── KEY_RESULTS.json           # required when key results are naturally structured
│   └── KEY_RESULTS.csv            # when tabular data is a natural representation
├── evidence/
│   └── EVIDENCE_MANIFEST.json
├── artifacts/
└── logs/
```

`reports/` is a compact human-attention surface, not a raw dump. `results/` preserves machine-readable key results where appropriate. `evidence/EVIDENCE_MANIFEST.json` indexes decisive evidence and lineage. Raw logs stay in `logs/`; generated products stay in `artifacts/`.
