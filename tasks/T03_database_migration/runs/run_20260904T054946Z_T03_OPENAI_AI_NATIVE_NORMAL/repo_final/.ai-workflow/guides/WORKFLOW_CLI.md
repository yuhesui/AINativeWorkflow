# `aw` Runtime Guide

The CLI is deterministic lifecycle tooling. It does not decide scientific meaning.

Typical operations:

```text
python .ai-workflow/aw.py --help
python .ai-workflow/aw.py status
python .ai-workflow/aw.py validate
python .ai-workflow/aw.py recover
python .ai-workflow/aw.py demo
```

Use the actual `--help` output as the command authority for the installed version. Semantic Plan/Phase/DIC decisions and the **initial EPS/prompt graph** belong to Main; runtime prompt compilation, execution state, and bounded repair EPS revisions belong to the coding-agent Orchestrator.


## Main-authored Phase ZIP import

A Main session may return one self-contained Phase ZIP. Import it with:

```bash
python .ai-workflow/aw.py --root . phase import MAIN_PHASE.zip
```

The importer validates safe paths, requires `PHASE_MANIFEST.json` plus the Core DIC views, installs the Phase below root `phases/<phase_id>/`, registers the DIC and optional initial EPS in `STATE.json`, and materializes the predictable reports/results/evidence/artifacts/logs/EPS scaffold.
