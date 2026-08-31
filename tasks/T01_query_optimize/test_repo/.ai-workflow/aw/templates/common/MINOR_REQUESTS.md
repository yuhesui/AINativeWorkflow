# Minor Requests

Phase-local append-only ledger managed by `aw minor`.

Minor covers frequent reversible, non-architectural work: links, headings, status synchronization,
small test expectation repairs, path updates and concise report extraction.

Escalate architecture, dependencies, public interfaces, data policy, scientific method, experiment
configuration, permissions, external actions, evidence/claims, release or broad ambiguity.

Typical commands:

```bash
aw minor from-user --input "fix broken links and update status"
aw minor add --type fix --title "..." --request "..." --files "..." --checks "..."
aw minor show --id MF-01
aw minor approve --id MF-01 --confirmation "GO MinorFix 01"
aw minor done --id MF-01 --files "..." --checks "..." --log "minor/logs/MF-01.md"
aw minor promote --id MF-02 --to-prompt 07A
```
