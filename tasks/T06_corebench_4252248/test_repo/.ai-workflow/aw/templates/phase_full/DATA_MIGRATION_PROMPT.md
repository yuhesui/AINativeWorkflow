# Major Data Migration Prompt Reference

{{WORKFLOW_CONTEXT}}

Inventory source read-only; classify rights, secrets, links, paths and sizes; create a deterministic
dry-run plan; prove capacity and rollback; copy to a private staging area; hash source/destination;
register provenance; validate transformation and no-lookahead rules; never mutate the external source;
never silently substitute data; require independent verification before deletion or promotion.
