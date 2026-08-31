# Run results — T04_recli

Store normalized result records separately from the full run repositories.

Recommended per-run files:

```text
run_results/<RUN_ID>/
├── SCORE.json
├── GRADER_RAW.*
├── METRICS.json
├── RECOVERY.json        # when state loss applies
└── SUMMARY.md
```

Native benchmark metrics remain authoritative; normalized completion scores must retain the raw/native score alongside them.
