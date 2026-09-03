# CLI compatibility

The canonical hierarchy is available through either:

```bash
python .ai-workflow/aw_hierarchy.py ...
python -m aw.hierarchy_cli --root . ...   # with .ai-workflow on PYTHONPATH
.ai-workflow/bin/aw-hierarchy ...
```

These entry points avoid rewriting a legacy dispatcher whose command surface may be used by existing projects. Existing v5.6.31 commands remain intact. The hierarchical Python API is exported from `aw` where normal package imports are used. A future major release may make `aw hierarchy` the only spelling after downstream migration tests.
