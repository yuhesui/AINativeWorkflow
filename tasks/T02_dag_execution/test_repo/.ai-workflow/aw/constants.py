from __future__ import annotations
import re

VERSION = "5.6.35"
SPECIFICATION_REVISION = "5.6"
TARGET_MODEL_FAMILY = "GPT-5.6"
PHASE_NAME_RE = re.compile(r"^phase_[A-Za-z0-9][A-Za-z0-9_-]*$")
PROMPT_ID_RE = re.compile(r"^(?:GOAL|000|001|\d{2,3}[A-Z]?)$")
REQUEST_ID_RE = re.compile(r"^RQ-(\d{3,})$")
REQUEST_LINE_RE = re.compile(r"^- \[([ xX])\] (RQ-\d{3,}) — (.+)$")
GOAL_LINE_RE = re.compile(r"^- \[([ xX])\] (G-\d{3,}) — (.+)$")
MINOR_ID_RE = re.compile(r"^(MF|MU|MR)-(\d{2,})$")
PROMPT_STATUSES = {
    "planned", "ready", "running", "completed", "integrated", "verified",
    "blocked", "failed", "superseded",
}
DEPENDENCY_DONE = {"integrated", "verified"}
MINOR_TERMINAL = {"completed", "blocked", "failed", "escalated"}
MINOR_APPROVED = {"approved", "approved_by_phase"}
MINOR_PREFIX = {"fix": "MF", "update": "MU", "report": "MR"}
MINOR_TYPE = {"MF": "fix", "MU": "update", "MR": "report"}
MODES = {"goal", "structured"}
EXECUTION_LEVELS = {"low", "mid", "high", "xhigh", "ultra"}
RESEARCH_LEVELS = {"none", "low", "mid", "high", "max"}
TEST_PROFILES = {"focused", "affected", "integration", "full"}
ROUTING_PROFILES = {"all", "chatgpt_only", "claude_only", "custom"}
BACKEND_KINDS = {"unspecified", "fixture", "smoke", "real", "resource_qualification"}
EVIDENCE_LEVELS = {"none", "implementation", "smoke", "pilot", "locked", "verified"}
MODEL_PROFILES = {
    "main", "orchestrator", "worker", "worker_complex", "minor", "verifier", "research"
}
ROLE_GUIDES = {
    "main": ".ai-workflow/docs/MAIN.md",
    "orchestrator": ".ai-workflow/docs/ORCHESTRATOR.md",
    "worker": ".ai-workflow/docs/WORKER.md",
    "worker_complex": ".ai-workflow/docs/WORKER.md",
    "minor": ".ai-workflow/docs/MINOR.md",
    "verifier": ".ai-workflow/docs/VERIFIER.md",
    "research": ".ai-workflow/docs/RESEARCH.md",
}
MANAGED_CONTEXT_BEGIN = "<!-- AW:CONFIG:BEGIN -->"
MANAGED_CONTEXT_END = "<!-- AW:CONFIG:END -->"
