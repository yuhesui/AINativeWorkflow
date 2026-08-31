# Full run repositories — T05_rlMetaMazeMisc

Each run gets its own directory. **The final state of the full scored sub-repository must be retained here**, not merely a diff.

Recommended layout:

```text
runs/<RUN_ID>/
├── RUN.json
├── repo_initial/        # optional immutable initial snapshot/hash reference
├── repo_final/          # REQUIRED complete final Direct/AI-Native repository
├── main/                # Main prompts/handoffs/exports permitted by protocol
├── executors/           # Codex/Claude trajectories and tool logs
├── state_loss/          # trigger/recovery artifacts where applicable
└── evidence/            # hashes/manifests/raw evidence pointers
```

`repo_final/` for AI-Native must contain the final mutated `.ai-workflow/` state, including generated Plan/Phase/DIC/EPS artifacts. Direct `repo_final/` must not contain `.ai-workflow/`.
