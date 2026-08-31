# Global reference material

This directory stores **global provenance and explanatory material** used to audit the experiment but not automatically exposed to scored agents.

```text
reference_material/
└── ai_native_workflow/
    ├── source_package/     # full current AI-Native Workflow package ZIP
    ├── papers/             # technical report + workshop manuscript snapshots
    ├── .aiexplainer/       # machine-facing index/read-order/manifest
    ├── AI_NATIVE_WORKFLOW_FULL_AI_EXPLAINER.zip
    └── prompting/          # provider/source provenance added during setup
```

Task-specific papers/specifications live under each task capsule's own `reference_material/` directory.
The run harness decides which task references are agent-visible; global reference material is not mounted into Direct runs by default.
