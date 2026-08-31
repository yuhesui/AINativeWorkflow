__version__ = "5.6.35"

# AIWF hierarchical API exports
try:
    from .hierarchy import WorkflowStore, WorkflowError, MaterialEscalationRequired, canonical_role
except Exception:
    # Preserve legacy imports even if a partially migrated environment lacks optional state.
    pass
