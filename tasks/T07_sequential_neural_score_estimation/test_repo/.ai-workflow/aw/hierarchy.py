"""Canonical Goal -> Plan -> Phase -> DIC -> EPS -> Prompt/Run -> Action runtime.

The module uses only the Python standard library.  JSON is the durable wire
format so that a fresh session can recover authority and lineage from the
package without relying on chat history.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from enum import Enum
import argparse
import copy
import datetime as _dt
import hashlib
import json
import os
import re
import sys
import uuid

SCHEMA_VERSION = "5.6.35"
CANONICAL_ROLES = ("Main", "Theory", "Experiment")
ROLE_ALIASES = {
    "main": "Main",
    "orchestrator": "Main",
    "manager": "Main",
    "theory": "Theory",
    "theorist": "Theory",
    "researcher": "Theory",
    "experiment": "Experiment",
    "experimentalist": "Experiment",
    "engineer": "Experiment",
}
MATERIAL_ESCALATION_KINDS = {
    "objective_change",
    "authority_change",
    "scientific_claim_change",
    "protocol_change",
    "destructive_external",
    "release_change",
    "submission_change",
    "purchase_or_paid_compute",
    "credentials_or_private_system",
}
VERIFICATION_OUTCOMES = ("accept", "repair", "replan", "escalate")
LANE_NAMES = ("minor", "research", "verification", "checkpoints")
LANE_MODES = ("off", "auto", "on")
DEFAULT_LANE_POLICY = {name: "auto" for name in LANE_NAMES}
DEFAULT_DIC_VIEWS = {
    "README.md": "on",
    "REQUESTS.md": "on",
    "PLAN.md": "on",
    "ARCHITECTURE.md": "auto",
    "TEST_MATRIX.md": "auto",
}
DEFAULT_REPORT_POLICY = {
    "always_present": True,
    "flat": True,
    "max_files": 10,
    "include_human_report": True,
    "include_key_raw_results": True,
}

class WorkflowError(RuntimeError):
    pass

class MaterialEscalationRequired(WorkflowError):
    pass

class Status(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETE = "complete"
    BLOCKED = "blocked"
    CHECKPOINT_DUE = "checkpoint_due"
    ESCALATED = "escalated"


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()

def _slug(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return value[:48] or "item"

def _id(prefix: str, title: str = "") -> str:
    return f"{prefix}-{_slug(title)}-{uuid.uuid4().hex[:8]}"

def canonical_role(role: str) -> str:
    if role in CANONICAL_ROLES:
        return role
    key = role.strip().lower()
    if key not in ROLE_ALIASES:
        raise WorkflowError(f"Unknown role {role!r}; use Main, Theory, or Experiment")
    return ROLE_ALIASES[key]

def _json_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

@dataclass(frozen=True)
class CheckpointPolicy:
    interval: int = 7
    ordinary_autonomy: bool = True
    require_human_resolution: bool = True

    def validate(self) -> None:
        if not 1 <= self.interval <= 100:
            raise WorkflowError("checkpoint interval must be between 1 and 100")

class WorkflowStore:
    """Filesystem-backed authority store.

    `.ai-workflow/STATE.json` is the small authoritative index.  Full DICs,
    EPS records, action records, and evidence live below `.ai-workflow/runtime`
    and are content-addressed from the index.
    """

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        self.aw = self.root / ".ai-workflow"
        self.state_path = self.aw / "STATE.json"
        self.runtime = self.aw / "runtime"

    def exists(self) -> bool:
        return self.state_path.exists()

    def init(self, checkpoint_interval: int = 7, force: bool = False) -> dict[str, Any]:
        policy = CheckpointPolicy(checkpoint_interval)
        policy.validate()
        self.aw.mkdir(parents=True, exist_ok=True)
        self.runtime.mkdir(parents=True, exist_ok=True)
        if self.exists() and not force:
            return self.load()
        state = {
            "schema_version": SCHEMA_VERSION,
            "package_root": ".",
            "authority": {
                "source": ".ai-workflow/STATE.json",
                "principle": "package state overrides chat recollection",
            },
            "roles": {
                "canonical": list(CANONICAL_ROLES),
                "aliases": ROLE_ALIASES,
            },
            "governance": {
                "checkpoint_interval": checkpoint_interval,
                "ordinary_autonomy": True,
                "human_approval_boundary": "Plan plus periodic/material checkpoints",
                "machine_execution_boundary": "Phase/DIC/EPS/Prompt/Action",
                "material_escalation_kinds": sorted(MATERIAL_ESCALATION_KINDS),
                "phase_lanes": dict(DEFAULT_LANE_POLICY),
                "dic_views": dict(DEFAULT_DIC_VIEWS),
                "reports": dict(DEFAULT_REPORT_POLICY),
            },
            "active_plan_id": None,
            "plans": {},
            "checkpoints": [],
            "escalations": [],
            "evidence_index": {},
            "legacy": {"migration_sources": [], "aliases_enabled": True},
            "events": [],
            "updated_at": _now(),
        }
        self.save(state, event={"kind": "package_initialized"})
        return state

    def load(self) -> dict[str, Any]:
        if not self.state_path.exists():
            raise WorkflowError(f"No canonical state at {self.state_path}; run init")
        with self.state_path.open(encoding="utf-8") as f:
            state = json.load(f)
        if str(state.get("schema_version", "")).split(".")[:2] != SCHEMA_VERSION.split(".")[:2]:
            raise WorkflowError("unsupported state schema; run migrate")
        return state

    def save(self, state: dict[str, Any], event: Mapping[str, Any] | None = None) -> None:
        state = copy.deepcopy(state)
        state["updated_at"] = _now()
        if event:
            item = dict(event)
            item.setdefault("at", _now())
            state.setdefault("events", []).append(item)
            state["events"] = state["events"][-500:]
        self.aw.mkdir(parents=True, exist_ok=True)
        tmp = self.state_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        os.replace(tmp, self.state_path)

    def _plan(self, state: dict[str, Any], plan_id: str | None = None) -> dict[str, Any]:
        pid = plan_id or state.get("active_plan_id")
        if not pid or pid not in state.get("plans", {}):
            raise WorkflowError("No active plan")
        return state["plans"][pid]

    def create_plan(self, title: str, goal: str, *, checkpoint_interval: int | None = None,
                    plan_id: str | None = None) -> str:
        state = self.load() if self.exists() else self.init()
        pid = plan_id or _id("plan", title)
        if pid in state["plans"]:
            raise WorkflowError(f"plan already exists: {pid}")
        interval = checkpoint_interval or state["governance"]["checkpoint_interval"]
        CheckpointPolicy(interval).validate()
        plan = {
            "id": pid,
            "title": title,
            "goal": goal,
            "status": Status.DRAFT.value,
            "approved_at": None,
            "checkpoint_interval": interval,
            "completed_since_checkpoint": 0,
            "phases": {},
            "phase_order": [],
            "active_phase_id": None,
            "created_at": _now(),
            "revision": 1,
        }
        state["plans"][pid] = plan
        state["active_plan_id"] = pid
        self._ensure_plan_dirs(pid)
        self.save(state, {"kind": "plan_created", "plan_id": pid})
        return pid

    def approve_plan(self, plan_id: str | None = None, *, approved_by: str = "human") -> None:
        state = self.load()
        plan = self._plan(state, plan_id)
        if not plan["phases"]:
            raise WorkflowError("A Plan must contain at least one Phase before approval")
        plan["status"] = Status.APPROVED.value
        plan["approved_at"] = _now()
        plan["approved_by"] = approved_by
        self.save(state, {"kind": "plan_approved", "plan_id": plan["id"], "by": approved_by})

    def add_phase(self, title: str, objective: str, *, owner: str = "Main",
                  dependencies: Sequence[str] = (), materiality: str = "ordinary",
                  plan_id: str | None = None, phase_id: str | None = None,
                  acceptance: Sequence[Mapping[str, Any] | str] = (),
                  lane_policy: Mapping[str, str] | None = None,
                  dic_views: Mapping[str, str] | None = None) -> str:
        state = self.load()
        plan = self._plan(state, plan_id)
        if plan["status"] != Status.DRAFT.value:
            raise WorkflowError("Change an approved Plan only through replan/escalation")
        owner = canonical_role(owner)
        phid = phase_id or _id("phase", title)
        if phid in plan["phases"]:
            raise WorkflowError(f"phase already exists: {phid}")
        unknown = set(dependencies) - set(plan["phases"])
        if unknown:
            raise WorkflowError(f"unknown phase dependencies: {sorted(unknown)}")
        lanes = dict(DEFAULT_LANE_POLICY)
        lanes.update(dict(lane_policy or {}))
        for lane, mode in lanes.items():
            if lane not in LANE_NAMES or mode not in LANE_MODES:
                raise WorkflowError(f"invalid lane policy {lane}={mode}; lanes={LANE_NAMES}, modes={LANE_MODES}")
        views = dict(DEFAULT_DIC_VIEWS)
        views.update(dict(dic_views or {}))
        for name, mode in views.items():
            if mode not in LANE_MODES:
                raise WorkflowError(f"invalid DIC view mode {name}={mode}; use off, auto, or on")
        phase = {
            "id": phid,
            "title": title,
            "objective": objective,
            "owner": owner,
            "materiality": materiality,
            "dependencies": list(dependencies),
            "status": Status.PENDING.value,
            "dic_id": None,
            "eps_ids": [],
            "action_ids": [],
            "verification": [],
            "acceptance": [self._predicate(x, i) for i, x in enumerate(acceptance)],
            "lane_policy": lanes,
            "dic_views": views,
            "report_policy": dict(DEFAULT_REPORT_POLICY),
            "evidence": [],
            "attempt": 0,
            "created_at": _now(),
            "completed_at": None,
        }
        plan["phases"][phid] = phase
        plan["phase_order"].append(phid)
        self._ensure_phase_dirs(plan["id"], phid, phase=phase)
        self._init_reports(plan["id"], phid, phase)
        self.save(state, {"kind": "phase_added", "plan_id": plan["id"], "phase_id": phid})
        return phid

    @staticmethod
    def _predicate(value: Mapping[str, Any] | str, idx: int) -> dict[str, Any]:
        if isinstance(value, str):
            return {"id": f"ac-{idx+1}", "predicate": value, "kind": "human_or_tool", "status": "pending"}
        result = dict(value)
        result.setdefault("id", f"ac-{idx+1}")
        result.setdefault("kind", "human_or_tool")
        result.setdefault("status", "pending")
        if "predicate" not in result:
            raise WorkflowError("acceptance item requires predicate")
        return result

    def create_dic(self, phase_id: str, *, subgoal: str | None = None,
                   constraints: Sequence[str] = (), authority: Sequence[str] = (),
                   evidence_requirements: Sequence[str] = (), exclusions: Sequence[str] = (),
                   escalation_triggers: Sequence[str] = (), plan_id: str | None = None,
                   readme_text: str | None = None, requests_text: str | None = None,
                   plan_text: str | None = None, architecture_text: str | None = None,
                   test_matrix_text: str | None = None,
                   custom_views: Mapping[str, str] | None = None) -> str:
        """Create one multi-view DIC package for the whole Phase.

        README/REQUESTS/PLAN are durable views of the same Phase contract. PLAN is
        intentionally an execution plan: prompt nodes, dependencies, parallel
        subagent batches, merge points and review branches. ARCHITECTURE and
        TEST_MATRIX are optional views. Custom Markdown views are first-class.
        """
        state = self.load()
        plan = self._plan(state, plan_id)
        phase = self._phase(plan, phase_id)
        dic_id = _id("dic", phase["title"])
        ddir = self._phase_dir(plan["id"], phase_id) / "DIC"
        ddir.mkdir(parents=True, exist_ok=True)
        objective = subgoal or phase["objective"]
        constraints = list(constraints)
        authority = list(authority)
        evidence_requirements = list(evidence_requirements)
        exclusions = list(exclusions)
        escalation_triggers = list(escalation_triggers)

        if readme_text is None:
            readme_text = f"""# {phase['title']} — DIC\n\n## Summary\n\n{objective}\n\n- **Owner:** {phase['owner']}\n- **Plan:** `{plan['id']}`\n- **Phase:** `{phase_id}`\n- **Dependencies:** {', '.join(phase['dependencies']) or 'none'}\n\n## DIC views\n\n- `REQUESTS.md` — specific goals/acceptance targets to be achieved.\n- `PLAN.md` — durable execution plan: prompt graph, dependencies, parallel subagent batches, merge/review points and conditional branches.\n- `ARCHITECTURE.md` — target repository/system architecture when this Phase changes architecture.\n- `TEST_MATRIX.md` — test/experiment/evaluation matrix when useful.\n- Additional user-defined Markdown files are permitted as first-class DIC views.\n\nEPS files instantiate planned prompt nodes just in time; they do not replace this DIC.\n"""
        if requests_text is None:
            lines = [f"# {phase['title']} — Requests", "", "These are goals to resolve, not an execution sequence.", ""]
            if phase.get("acceptance"):
                for item in phase["acceptance"]:
                    lines += [f"## {item['id']}", "", item.get("predicate", ""), "", f"- Status: `{item.get('status','pending')}`", ""]
            else:
                lines += ["## R01 — Phase objective", "", objective, "", "- Status: `OPEN`", ""]
            if evidence_requirements:
                lines += ["## Required evidence", ""] + [f"- `{x}`" for x in evidence_requirements] + [""]
            requests_text = "\n".join(lines)
        if plan_text is None:
            plan_text = f"""# {phase['title']} — Execution Plan\n\n## Execution objective\n\n{objective}\n\n## Prompt graph\n\nDefine the durable prompt/run graph here. For each node record: objective, Request IDs, dependencies, owner/profile, whether it is a parallel subagent job, expected outputs, local checks, merge point, and conditional repair/review branches.\n\n| ID | Objective | Requests | Depends on | Parallel/subagent group | Owner/profile | Outputs | Merge/review |\n|---|---|---|---|---|---|---|---|\n| P01 | Inspect current authoritative state and refine the execution graph | — | — | — | {phase['owner']} | execution-ready context | update this plan if needed |\n\n## Parallelism\n\nParallelize only when dependencies are satisfied, write scopes are compatible, failures are independently recoverable, and the merge point is explicit.\n\n## EPS relationship\n\nEach planned prompt node may be instantiated one or more times by EPS as state changes. Repairs/retries normally create a new EPS/run instance while leaving this durable plan intact.\n"""
        core = {"README.md": readme_text, "REQUESTS.md": requests_text, "PLAN.md": plan_text}
        for name, text in core.items():
            (ddir / name).write_text(text.rstrip()+"\n", encoding="utf-8")

        view_modes = phase.get("dic_views", DEFAULT_DIC_VIEWS)
        if architecture_text is not None or view_modes.get("ARCHITECTURE.md") == "on":
            text = architecture_text or f"# {phase['title']} — Target Architecture\n\nDocument the new repository/system architecture only where this Phase changes it. Include current → target structure, interfaces, migrations, invariants and ownership.\n"
            (ddir / "ARCHITECTURE.md").write_text(text.rstrip()+"\n", encoding="utf-8")
        if test_matrix_text is not None or view_modes.get("TEST_MATRIX.md") == "on":
            text = test_matrix_text or f"# {phase['title']} — Test / Experiment Matrix\n\nDefine concrete batches/combinations to execute or falsify. This may be a software test matrix, theory audit matrix, or an experimental algorithm × task × seed/fault matrix.\n"
            (ddir / "TEST_MATRIX.md").write_text(text.rstrip()+"\n", encoding="utf-8")

        custom = {}
        for raw_name, content in dict(custom_views or {}).items():
            name = self._safe_dic_view_name(raw_name)
            if name in {"MANIFEST.json", *core.keys()}:
                raise WorkflowError(f"custom DIC view collides with reserved name: {name}")
            (ddir / name).write_text(str(content).rstrip()+"\n", encoding="utf-8")
            custom[name] = {"kind": "custom", "required": True}

        views = {}
        for f in sorted(ddir.iterdir()):
            if f.is_file() and f.name != "MANIFEST.json":
                views[f.name] = {"kind": "custom" if f.name in custom else self._dic_view_kind(f.name), "required": f.name in core or bool(custom.get(f.name,{}).get("required"))}
        manifest = {
            "schema": "ai-native-workflow/dic-package/2",
            "id": dic_id,
            "plan_id": plan["id"],
            "phase_id": phase_id,
            "owner": phase["owner"],
            "objective": objective,
            "constraints": constraints,
            "authority": authority,
            "acceptance_conditions": phase["acceptance"],
            "evidence_requirements": evidence_requirements,
            "out_of_scope": exclusions,
            "escalation_triggers": escalation_triggers,
            "dependencies": phase["dependencies"],
            "views": views,
            "custom_views_allowed": True,
            "created_at": _now(),
        }
        mpath = ddir / "MANIFEST.json"
        mpath.write_text(json.dumps(manifest, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
        phase["dic_id"] = dic_id
        phase["dic_path"] = str(ddir.relative_to(self.root))
        phase["dic_manifest_path"] = str(mpath.relative_to(self.root))
        phase["dic_hash"] = self._directory_hash(ddir)
        self.save(state, {"kind": "dic_created", "plan_id": plan["id"], "phase_id": phase_id, "dic_id": dic_id})
        return dic_id

    def add_dic_view(self, phase_id: str, name: str, content: str, *, required: bool = False,
                     plan_id: str | None = None) -> str:
        state = self.load(); plan = self._plan(state, plan_id); phase = self._phase(plan, phase_id)
        if not phase.get("dic_path"):
            raise WorkflowError("Create the DIC package before adding a custom view")
        name = self._safe_dic_view_name(name)
        ddir = self.root / phase["dic_path"]
        path = ddir / name
        path.write_text(content.rstrip()+"\n", encoding="utf-8")
        manifest = json.loads((ddir / "MANIFEST.json").read_text(encoding="utf-8"))
        manifest.setdefault("views", {})[name] = {"kind": "custom", "required": bool(required)}
        (ddir / "MANIFEST.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
        phase["dic_hash"] = self._directory_hash(ddir)
        self.save(state, {"kind": "dic_view_added", "phase_id": phase_id, "view": name})
        return str(path.relative_to(self.root))

    def generate_eps(self, phase_id: str, actions: Sequence[Mapping[str, Any]], *,
                     executor: str | None = None, plan_id: str | None = None) -> str:
        """Instantiate durable DIC/PLAN nodes into a disposable execution stack.

        `actions` is retained as the public argument for compatibility; each item is
        treated as an EPS prompt/run node and may declare dependencies, parallel_group,
        subagent, plan_node_id, model_profile and prompt/instruction text.
        """
        state = self.load(); plan = self._plan(state, plan_id); phase = self._phase(plan, phase_id)
        if not phase.get("dic_id"):
            raise WorkflowError("Create the DIC package before generating EPS")
        eps_id = _id("eps", phase["title"])
        normalized=[]; known=set()
        for i, action in enumerate(actions):
            node=dict(action)
            node.setdefault("id", f"P{i+1:02d}")
            nid=str(node["id"])
            if nid in known: raise WorkflowError(f"duplicate EPS node id: {nid}")
            known.add(nid)
            node.setdefault("plan_node_id", nid)
            node.setdefault("depends_on", [])
            node.setdefault("parallel_group", None)
            node.setdefault("subagent", False)
            node.setdefault("acceptance", "local observable checks satisfy the DIC request(s)")
            node.setdefault("status", "pending")
            normalized.append(node)
        for node in normalized:
            missing=set(node.get("depends_on",[]))-known
            if missing: raise WorkflowError(f"EPS node {node['id']} has unknown dependencies: {sorted(missing)}")
        edir=self._phase_dir(plan["id"], phase_id)/"EPS"; pdir=edir/"prompts"
        pdir.mkdir(parents=True, exist_ok=True)
        for node in normalized:
            body = node.get("prompt") or node.get("instruction") or node.get("operation")
            if body:
                safe=_slug(str(node["id"]))
                prompt_path=pdir/f"{eps_id}__{safe}.md"
                prompt_path.write_text(
                    f"# EPS {eps_id} — {node['id']}\n\n"
                    f"- Plan node: `{node.get('plan_node_id')}`\n"
                    f"- Depends on: {', '.join(node.get('depends_on',[])) or 'none'}\n"
                    f"- Parallel group: `{node.get('parallel_group') or 'none'}`\n"
                    f"- Subagent: `{bool(node.get('subagent'))}`\n\n"
                    f"## Run instruction\n\n{body}\n",
                    encoding="utf-8")
                node["prompt_file"] = str(prompt_path.relative_to(self.root))
        eps = {
            "schema": "ai-native-workflow/eps/2",
            "id": eps_id,
            "dic_id": phase["dic_id"],
            "phase_id": phase_id,
            "plan_id": plan["id"],
            "executor": canonical_role(executor or phase["owner"]),
            "disposable": True,
            "generated_at": _now(),
            "nodes": normalized,
            "actions": normalized,
            "stop_conditions": ["DIC requests accepted", "material escalation", "blocked dependency", "budget boundary"],
        }
        path=edir/f"{eps_id}.json"
        path.write_text(json.dumps(eps, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
        phase["eps_ids"].append(eps_id); phase.setdefault("eps_paths",{})[eps_id]=str(path.relative_to(self.root))
        self.save(state, {"kind":"eps_generated","plan_id":plan["id"],"phase_id":phase_id,"eps_id":eps_id})
        return eps_id

    def start_phase(self, phase_id: str, *, plan_id: str | None = None) -> None:
        state = self.load()
        plan = self._plan(state, plan_id)
        if plan["status"] == Status.CHECKPOINT_DUE.value:
            raise WorkflowError("Periodic checkpoint is due before further autonomous progression")
        if plan["status"] == Status.ESCALATED.value:
            raise MaterialEscalationRequired("Resolve material escalation first")
        if plan["status"] != Status.APPROVED.value:
            raise WorkflowError("Plan must be approved")
        phase = self._phase(plan, phase_id)
        if phase["status"] not in (Status.PENDING.value, Status.BLOCKED.value):
            raise WorkflowError(f"phase cannot start from {phase['status']}")
        incomplete=[d for d in phase["dependencies"] if plan["phases"][d]["status"] != Status.COMPLETE.value]
        if incomplete:
            phase["status"] = Status.BLOCKED.value
            self.save(state, {"kind":"phase_blocked","phase_id":phase_id,"dependencies":incomplete})
            raise WorkflowError(f"incomplete dependencies: {incomplete}")
        if not phase.get("dic_id"):
            self.save(state)
            self.create_dic(phase_id, plan_id=plan["id"])
            state = self.load(); plan=self._plan(state,plan["id"]); phase=self._phase(plan,phase_id)
        phase["status"] = Status.ACTIVE.value
        phase["attempt"] += 1
        phase["started_at"] = _now()
        plan["active_phase_id"] = phase_id
        self.save(state, {"kind": "phase_started", "plan_id": plan["id"], "phase_id": phase_id})

    def record_action(self, phase_id: str, *, eps_id: str, action: str, result: str,
                      tool: str = "unspecified", status: str = "complete",
                      evidence_paths: Sequence[str] = (), prompt_node_id: str | None = None,
                      plan_id: str | None = None) -> str:
        state=self.load(); plan=self._plan(state,plan_id); phase=self._phase(plan,phase_id)
        if eps_id not in phase.get("eps_ids",[]):
            raise WorkflowError("EPS is not in phase lineage")
        aid=_id("act",action)
        record={
            "schema":"ai-native-workflow/action/1", "id":aid, "plan_id":plan["id"],
            "phase_id":phase_id,"dic_id":phase["dic_id"],"eps_id":eps_id,
            "prompt_node_id": prompt_node_id,
            "action":action,"tool":tool,"result":result,"status":status,
            "evidence_paths":list(evidence_paths),"at":_now(),
        }
        pdir=self._phase_dir(plan["id"],phase_id)/"actions"; pdir.mkdir(parents=True,exist_ok=True)
        path=pdir/f"{aid}.json"; path.write_text(json.dumps(record,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        phase["action_ids"].append(aid); phase.setdefault("action_paths",{})[aid]=str(path.relative_to(self.root))
        for ep in evidence_paths:
            state.setdefault("evidence_index",{})[ep]={"phase_id":phase_id,"action_id":aid,"recorded_at":_now()}
        self._append_raw_report(plan["id"], phase_id, record)
        self._update_report_manifest(plan["id"], phase_id, phase)
        self.save(state,{"kind":"action_recorded","phase_id":phase_id,"action_id":aid})
        return aid

    def verify(self, phase_id: str, outcome: str, *, rationale: str,
               evidence: Sequence[str] = (), independent: bool = False,
               plan_id: str | None = None) -> None:
        if outcome not in VERIFICATION_OUTCOMES:
            raise WorkflowError(f"outcome must be one of {VERIFICATION_OUTCOMES}")
        state=self.load(); plan=self._plan(state,plan_id); phase=self._phase(plan,phase_id)
        item={"outcome":outcome,"rationale":rationale,"evidence":list(evidence),
              "independent":bool(independent),"at":_now()}
        phase.setdefault("verification",[]).append(item)
        if outcome == "repair": phase["status"] = Status.ACTIVE.value
        elif outcome == "replan":
            self._raise_escalation_in_state(state,plan,"protocol_change",f"Replan requested for {phase_id}: {rationale}",phase_id)
        elif outcome == "escalate":
            self._raise_escalation_in_state(state,plan,"scientific_claim_change",rationale,phase_id)
        self.save(state,{"kind":"verification","phase_id":phase_id,"outcome":outcome})

    def complete_phase(self, phase_id: str, *, evidence: Sequence[str] = (),
                       acceptance_results: Mapping[str, bool] | None = None,
                       plan_id: str | None = None, allow_empty_acceptance: bool = True) -> dict[str, Any]:
        state=self.load(); plan=self._plan(state,plan_id); phase=self._phase(plan,phase_id)
        if phase["status"] != Status.ACTIVE.value:
            raise WorkflowError("Only an active phase can complete")
        acceptance_results=dict(acceptance_results or {})
        failed=[]
        for pred in phase.get("acceptance",[]):
            ok=acceptance_results.get(pred["id"])
            if ok is None and not allow_empty_acceptance: failed.append(pred["id"])
            elif ok is False: failed.append(pred["id"])
            elif ok is True: pred["status"]="satisfied"
        if failed:
            raise WorkflowError(f"unsatisfied acceptance predicates: {failed}")
        phase["evidence"].extend(x for x in evidence if x not in phase["evidence"])
        report_errors = self._report_surface_issues(plan["id"], phase_id, phase)
        if report_errors:
            raise WorkflowError("report surface invalid: " + "; ".join(report_errors))
        phase["status"] = Status.COMPLETE.value
        phase["completed_at"] = _now()
        self._write_phase_report(plan["id"], phase_id, phase)
        self._update_report_manifest(plan["id"], phase_id, phase)
        plan["active_phase_id"] = None
        plan["completed_since_checkpoint"] += 1
        checkpoint=None
        if plan["completed_since_checkpoint"] >= plan["checkpoint_interval"]:
            checkpoint={
                "id":_id("checkpoint",plan["title"]),"kind":"periodic","plan_id":plan["id"],
                "after_phase_id":phase_id,"status":"due","created_at":_now(),
                "completed_phase_count":sum(1 for p in plan["phases"].values() if p["status"]==Status.COMPLETE.value),
            }
            state["checkpoints"].append(checkpoint)
            plan["status"] = Status.CHECKPOINT_DUE.value
        else:
            nxt=self._next_ready(plan)
            if nxt and state["governance"].get("ordinary_autonomy",True):
                # Marking active is a machine boundary; execution still creates its own EPS.
                plan["phases"][nxt]["status"] = Status.ACTIVE.value
                plan["phases"][nxt]["attempt"] += 1
                plan["phases"][nxt]["started_at"] = _now()
                if not plan["phases"][nxt].get("dic_id"):
                    # DIC creation requires a separate atomic save/call; leave pending active DIC creation to caller.
                    pass
                plan["active_phase_id"] = nxt
        if all(p["status"]==Status.COMPLETE.value for p in plan["phases"].values()):
            plan["status"]="complete"
        self.save(state,{"kind":"phase_completed","phase_id":phase_id,"checkpoint_id":checkpoint and checkpoint["id"]})
        return {"checkpoint":checkpoint,"next_phase_id":plan.get("active_phase_id"),"plan_status":plan["status"]}

    def resolve_checkpoint(self, checkpoint_id: str, *, decision: str = "continue",
                           notes: str = "", by: str = "human") -> None:
        state=self.load()
        cp=next((x for x in state.get("checkpoints",[]) if x["id"]==checkpoint_id),None)
        if cp is None: raise WorkflowError("unknown checkpoint")
        if cp["status"] != "due": raise WorkflowError("checkpoint already resolved")
        if decision not in ("continue","replan","stop"): raise WorkflowError("invalid decision")
        plan=self._plan(state,cp["plan_id"])
        cp.update({"status":"resolved","decision":decision,"notes":notes,"resolved_by":by,"resolved_at":_now()})
        plan["completed_since_checkpoint"]=0
        if decision=="continue":
            plan["status"]=Status.APPROVED.value
            nxt=self._next_ready(plan)
            if nxt:
                plan["phases"][nxt]["status"]=Status.ACTIVE.value
                plan["phases"][nxt]["attempt"]+=1
                plan["phases"][nxt]["started_at"]=_now(); plan["active_phase_id"]=nxt
        elif decision=="replan": plan["status"]=Status.ESCALATED.value
        else: plan["status"]="stopped"
        self.save(state,{"kind":"checkpoint_resolved","checkpoint_id":checkpoint_id,"decision":decision})

    def escalate(self, kind: str, reason: str, *, phase_id: str | None = None,
                 plan_id: str | None = None) -> str:
        state=self.load(); plan=self._plan(state,plan_id)
        eid=self._raise_escalation_in_state(state,plan,kind,reason,phase_id)
        self.save(state,{"kind":"material_escalation","escalation_id":eid,"phase_id":phase_id})
        return eid

    def _raise_escalation_in_state(self,state,plan,kind,reason,phase_id=None):
        if kind not in MATERIAL_ESCALATION_KINDS:
            raise WorkflowError(f"unknown material escalation kind: {kind}")
        eid=_id("escalation",kind)
        item={"id":eid,"kind":kind,"reason":reason,"plan_id":plan["id"],"phase_id":phase_id,
              "status":"open","created_at":_now()}
        state["escalations"].append(item); plan["status"]=Status.ESCALATED.value
        if phase_id and phase_id in plan["phases"]: plan["phases"][phase_id]["status"]=Status.ESCALATED.value
        return eid

    def resolve_escalation(self, escalation_id: str, *, decision: str, notes: str = "", by: str = "human") -> None:
        state=self.load(); esc=next((e for e in state["escalations"] if e["id"]==escalation_id),None)
        if not esc: raise WorkflowError("unknown escalation")
        esc.update({"status":"resolved","decision":decision,"notes":notes,"resolved_at":_now(),"resolved_by":by})
        plan=self._plan(state,esc["plan_id"])
        if decision=="continue":
            plan["status"]=Status.APPROVED.value
            if esc.get("phase_id") and esc["phase_id"] in plan["phases"]:
                plan["phases"][esc["phase_id"]]["status"]=Status.ACTIVE.value
                plan["active_phase_id"]=esc["phase_id"]
        elif decision=="replan": plan["status"]=Status.DRAFT.value; plan["revision"]+=1
        else: plan["status"]="stopped"
        self.save(state,{"kind":"escalation_resolved","escalation_id":escalation_id,"decision":decision})

    def lineage(self, phase_id: str, *, plan_id: str | None = None) -> dict[str, Any]:
        state=self.load(); plan=self._plan(state,plan_id); phase=self._phase(plan,phase_id)
        return {
            "goal":plan["goal"],"plan_id":plan["id"],"phase_id":phase_id,"dic_id":phase.get("dic_id"),
            "eps_ids":list(phase.get("eps_ids",[])),"action_ids":list(phase.get("action_ids",[])),
            "relation":"Action <= Prompt/Run <= EPS <= DIC <= Phase <= Plan <= Goal",
        }

    def recover(self) -> dict[str, Any]:
        state=self.load(); errors=[]; warnings=[]
        for pid,plan in state.get("plans",{}).items():
            seen=set()
            for phid in plan.get("phase_order",[]):
                if phid not in plan.get("phases",{}): errors.append(f"{pid}: missing phase {phid}"); continue
                phase=plan["phases"][phid]
                unknown=set(phase.get("dependencies",[]))-set(plan["phases"])
                if unknown: errors.append(f"{phid}: unknown dependencies {sorted(unknown)}")
                if phase.get("dic_path"):
                    p=self.root/phase["dic_path"]
                    if not p.exists(): errors.append(f"{phid}: missing DIC package")
                    else:
                        try:
                            if p.is_dir():
                                mp=p/"MANIFEST.json"
                                dic=json.loads(mp.read_text(encoding="utf-8"))
                                if dic.get("phase_id")!=phid: errors.append(f"{phid}: DIC lineage mismatch")
                                for required in ("README.md","REQUESTS.md","PLAN.md","MANIFEST.json"):
                                    if not (p/required).is_file(): errors.append(f"{phid}: missing DIC view {required}")
                                for name,meta in dic.get("views",{}).items():
                                    if meta.get("required") and not (p/name).is_file(): errors.append(f"{phid}: missing required custom DIC view {name}")
                                if phase.get("dic_hash") and self._directory_hash(p)!=phase["dic_hash"]: errors.append(f"{phid}: DIC hash mismatch")
                            else:
                                dic=json.loads(p.read_text(encoding="utf-8"))
                                if dic.get("phase_id")!=phid: errors.append(f"{phid}: DIC lineage mismatch")
                                warnings.append(f"{phid}: legacy single-file DIC; migrate to multi-view package")
                        except Exception as exc: errors.append(f"{phid}: invalid DIC: {exc}")
                errors.extend(f"{phid}: {x}" for x in self._report_surface_issues(pid, phid, phase))
                for eid,path in phase.get("eps_paths",{}).items():
                    p=self.root/path
                    if not p.exists(): errors.append(f"{phid}: missing EPS {eid}")
                    else:
                        try:
                            eps=json.loads(p.read_text(encoding="utf-8"))
                            if eps.get("dic_id")!=phase.get("dic_id"): errors.append(f"{phid}: EPS {eid} DIC mismatch")
                        except Exception as exc: errors.append(f"{phid}: invalid EPS {eid}: {exc}")
                seen.add(phid)
            if len(seen)!=len(plan.get("phases",{})): warnings.append(f"{pid}: phases outside phase_order")
        return {"ok":not errors,"errors":errors,"warnings":warnings,"state_path":str(self.state_path),
                "active_plan_id":state.get("active_plan_id"),"schema_version":state.get("schema_version")}

    def migrate_legacy(self) -> dict[str, Any]:
        state=self.load() if self.exists() else self.init()
        candidates=[]
        for pattern in ("GOAL.md","CURRENT_CONTEXT.md","**/GOAL.md","**/CURRENT_CONTEXT.md","**/*handoff*.md"):
            for p in self.root.glob(pattern):
                try:
                    rel=str(p.relative_to(self.root))
                    if rel.startswith(".ai-workflow/runtime/"): continue
                    candidates.append(rel)
                except Exception: pass
        candidates=sorted(set(candidates))
        state.setdefault("legacy",{})["migration_sources"]=candidates
        state["legacy"]["aliases_enabled"]=True
        state["legacy"]["migration_note"]="Legacy files are retained as evidence/context, not competing authority."
        self.save(state,{"kind":"legacy_migration_indexed","count":len(candidates)})
        return {"indexed":candidates,"canonical_state":str(self.state_path.relative_to(self.root))}

    def status(self) -> dict[str, Any]:
        state=self.load(); result={"schema_version":state["schema_version"],"active_plan_id":state.get("active_plan_id"),
                                  "open_escalations":[e for e in state.get("escalations",[]) if e["status"]=="open"],
                                  "due_checkpoints":[c for c in state.get("checkpoints",[]) if c["status"]=="due"]}
        if state.get("active_plan_id"):
            p=self._plan(state); result["plan"]={k:p.get(k) for k in ("id","title","status","active_phase_id","completed_since_checkpoint","checkpoint_interval")}
            result["phases"]=[{k:p["phases"][pid].get(k) for k in ("id","title","owner","status","dic_id")} for pid in p["phase_order"]]
        return result

    def render_prompt(self, role: str, phase_id: str, *, plan_id: str | None = None) -> str:
        role=canonical_role(role); state=self.load(); plan=self._plan(state,plan_id); phase=self._phase(plan,phase_id)
        dic={}
        if phase.get("dic_path"):
            dp=self.root/phase["dic_path"]
            if dp.is_dir() and (dp/"MANIFEST.json").is_file():
                dic=json.loads((dp/"MANIFEST.json").read_text(encoding="utf-8"))
            elif dp.is_file():
                dic=json.loads(dp.read_text(encoding="utf-8"))
        return f"""# {role} execution brief\n\n## Outcome\n{phase['objective']}\n\n## Authority and context\nPlan: {plan['title']}\nGoal: {plan['goal']}\nDIC package: {phase.get('dic_path','create before execution')}
Durable execution plan: {phase.get('dic_path','DIC')}/PLAN.md\nOwner: {phase['owner']}\nDependencies: {', '.join(phase['dependencies']) or 'none'}\n\n## Hard constraints\n""" + "\n".join(f"- {x}" for x in dic.get("constraints",[])) + f"""\n\n## Evidence and success criteria\n""" + "\n".join(f"- {x.get('predicate')}" for x in dic.get("acceptance_conditions",[])) + "\n" + "\n".join(f"- Evidence: {x}" for x in dic.get("evidence_requirements",[])) + f"""\n\n## Autonomy and escalation\nFollow the durable DIC/PLAN prompt graph, refining it only when ordinary execution evidence requires it, and generate disposable EPS run instances for the current state. Continue through ordinary local decisions. Escalate immediately only for a material objective, authority, scientific-claim, protocol, destructive/external, release, submission, purchase/paid-compute, or credential/private-system change. Do not expose private chain-of-thought; return decisions, evidence, artifacts, and concise rationale.\n\n## Deliverable\nUpdate package artifacts, record Action→Prompt/Run→EPS→DIC lineage, run local verification, and leave a reconstructable handoff.\n"""

    def set_lane(self, phase_id: str, lane: str, mode: str, *, plan_id: str | None = None) -> None:
        if lane not in LANE_NAMES or mode not in LANE_MODES:
            raise WorkflowError(f"lane must be one of {LANE_NAMES}, mode one of {LANE_MODES}")
        state=self.load(); plan=self._plan(state,plan_id); phase=self._phase(plan,phase_id)
        path=self._phase_dir(plan["id"],phase_id)/lane
        if mode == "off" and path.exists() and any(path.iterdir()):
            raise WorkflowError(f"cannot turn populated lane off without destructive cleanup: {lane}")
        phase.setdefault("lane_policy",dict(DEFAULT_LANE_POLICY))[lane]=mode
        if mode == "on": path.mkdir(parents=True,exist_ok=True)
        self.save(state,{"kind":"phase_lane_set","phase_id":phase_id,"lane":lane,"mode":mode})

    def materialize_lane(self, phase_id: str, lane: str, *, plan_id: str | None = None) -> str:
        if lane not in LANE_NAMES: raise WorkflowError(f"unknown lane: {lane}")
        state=self.load(); plan=self._plan(state,plan_id); phase=self._phase(plan,phase_id)
        mode=phase.get("lane_policy",DEFAULT_LANE_POLICY).get(lane,"auto")
        if mode == "off": raise WorkflowError(f"lane is disabled for this phase: {lane}")
        path=self._phase_dir(plan["id"],phase_id)/lane; path.mkdir(parents=True,exist_ok=True)
        self.save(state,{"kind":"phase_lane_materialized","phase_id":phase_id,"lane":lane})
        return str(path.relative_to(self.root))

    @staticmethod
    def _safe_dic_view_name(name: str) -> str:
        name=name.strip()
        if "/" in name or "\\" in name or name in {".","..",""}: raise WorkflowError("DIC custom views must be flat filenames")
        if not name.lower().endswith(".md"): name += ".md"
        if not re.fullmatch(r"[A-Za-z0-9_.-]+\.md", name): raise WorkflowError(f"invalid DIC view filename: {name}")
        return name

    @staticmethod
    def _dic_view_kind(name: str) -> str:
        return {"README.md":"summary","REQUESTS.md":"requests","PLAN.md":"execution_plan","ARCHITECTURE.md":"repository_architecture","TEST_MATRIX.md":"test_or_experiment_matrix"}.get(name,"custom")

    @staticmethod
    def _directory_hash(path: Path) -> str:
        h=hashlib.sha256()
        for f in sorted(x for x in path.rglob("*") if x.is_file()):
            h.update(str(f.relative_to(path)).encode("utf-8")); h.update(b"\0"); h.update(f.read_bytes()); h.update(b"\0")
        return h.hexdigest()

    def _init_reports(self, pid: str, phid: str, phase: Mapping[str, Any]) -> None:
        rdir=self._phase_dir(pid,phid)/"reports"; rdir.mkdir(parents=True,exist_ok=True)
        report=rdir/"REPORT.md"
        if not report.exists():
            report.write_text(f"# {phase['title']} — Phase Report\n\nStatus: `{phase.get('status','pending')}`\n\nThis is the compact human synthesis surface. Key merged raw results are preserved losslessly in `RAW_RESULTS.jsonl`; full forensic evidence remains in `logs/`, `evidence/`, and optional lanes.\n",encoding="utf-8")
        (rdir/"RAW_RESULTS.jsonl").touch(exist_ok=True)
        self._update_report_manifest(pid,phid,phase)

    def _append_raw_report(self, pid: str, phid: str, raw_record: Mapping[str, Any]) -> None:
        rdir=self._phase_dir(pid,phid)/"reports"; rdir.mkdir(parents=True,exist_ok=True)
        path=rdir/"RAW_RESULTS.jsonl"
        with path.open("a",encoding="utf-8") as f: f.write(json.dumps(dict(raw_record),ensure_ascii=False)+"\n")

    def _write_phase_report(self, pid: str, phid: str, phase: Mapping[str, Any]) -> None:
        rdir=self._phase_dir(pid,phid)/"reports"; rdir.mkdir(parents=True,exist_ok=True)
        lines=[f"# {phase['title']} — Phase Report","",f"- Status: `{phase.get('status')}`",f"- Owner: `{phase.get('owner')}`",f"- DIC: `{phase.get('dic_path')}`",f"- EPS instances: {len(phase.get('eps_ids',[]))}",f"- Recorded actions: {len(phase.get('action_ids',[]))}","","## Objective","",str(phase.get('objective','')),"","## Evidence"]
        lines += [f"- `{x}`" for x in phase.get("evidence",[])] or ["- none recorded"]
        lines += ["","## Verification"]
        for v in phase.get("verification",[]): lines.append(f"- **{v.get('outcome')}** — {v.get('rationale')}")
        if not phase.get("verification"): lines.append("- none recorded")
        lines += ["","## Raw result surface","","`RAW_RESULTS.jsonl` is a minimally transformed, lossless collation of recorded action results plus provenance. It is not an aggregate or prose summary.",""]
        (rdir/"REPORT.md").write_text("\n".join(lines),encoding="utf-8")

    def _update_report_manifest(self, pid: str, phid: str, phase: Mapping[str, Any]) -> None:
        rdir=self._phase_dir(pid,phid)/"reports"; rdir.mkdir(parents=True,exist_ok=True)
        files=[]
        for f in sorted(x for x in rdir.iterdir() if x.is_file() and x.name!="MANIFEST.json"):
            files.append({"name":f.name,"bytes":f.stat().st_size,"sha256":hashlib.sha256(f.read_bytes()).hexdigest()})
        manifest={"schema":"ai-native-workflow/phase-reports/1","phase_id":phid,"flat":True,"max_files":int(phase.get("report_policy",{}).get("max_files",10)),"raw_semantics":"lossless collation plus provenance; no averaging, rounding, paraphrase, favourable filtering or result rewriting","files":files,"updated_at":_now()}
        (rdir/"MANIFEST.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

    def _report_surface_issues(self, pid: str, phid: str, phase: Mapping[str, Any]) -> list[str]:
        rdir=self._phase_dir(pid,phid)/"reports"; issues=[]
        if not rdir.is_dir(): return ["missing always-present reports/ directory"]
        dirs=[p.name for p in rdir.iterdir() if p.is_dir()]
        if dirs: issues.append(f"reports/ must be flat; subdirectories found: {sorted(dirs)}")
        files=[p for p in rdir.iterdir() if p.is_file()]
        maximum=int(phase.get("report_policy",{}).get("max_files",10))
        if len(files)>maximum: issues.append(f"reports/ contains {len(files)} files; maximum is {maximum}")
        if not (rdir/"REPORT.md").is_file(): issues.append("missing reports/REPORT.md")
        if not (rdir/"RAW_RESULTS.jsonl").is_file(): issues.append("missing reports/RAW_RESULTS.jsonl")
        if not (rdir/"MANIFEST.json").is_file(): issues.append("missing reports/MANIFEST.json")
        return issues

    def _ensure_plan_dirs(self,pid): (self.runtime/"plans"/pid/"phases").mkdir(parents=True,exist_ok=True)
    def _ensure_phase_dirs(self,pid,phid,phase: Mapping[str,Any] | None=None):
        base=self._phase_dir(pid,phid)
        for rel in ("DIC","EPS/prompts","actions","logs","evidence","reports"): (base/rel).mkdir(parents=True,exist_ok=True)
        if phase:
            for lane,mode in phase.get("lane_policy",DEFAULT_LANE_POLICY).items():
                if mode == "on": (base/lane).mkdir(parents=True,exist_ok=True)
    def _phase_dir(self,pid,phid): return self.runtime/"plans"/pid/"phases"/phid
    @staticmethod
    def _phase(plan,phase_id):
        try: return plan["phases"][phase_id]
        except KeyError: raise WorkflowError(f"unknown phase: {phase_id}")
    @staticmethod
    def _next_ready(plan):
        for pid in plan["phase_order"]:
            p=plan["phases"][pid]
            if p["status"]==Status.PENDING.value and all(plan["phases"][d]["status"]==Status.COMPLETE.value for d in p["dependencies"]):
                return pid
        return None


def _read_json_arg(value: str) -> Any:
    p=Path(value)
    if p.exists(): return json.loads(p.read_text(encoding="utf-8"))
    return json.loads(value)

def build_parser() -> argparse.ArgumentParser:
    p=argparse.ArgumentParser(prog="aw-hierarchy",description="AI-Native Workflow hierarchical runtime")
    p.add_argument("--root",default=".")
    sp=p.add_subparsers(dest="cmd",required=True)
    q=sp.add_parser("init"); q.add_argument("--checkpoint-interval",type=int,default=7); q.add_argument("--force",action="store_true")
    q=sp.add_parser("status")
    q=sp.add_parser("recover")
    q=sp.add_parser("migrate")
    q=sp.add_parser("plan-create"); q.add_argument("title"); q.add_argument("goal"); q.add_argument("--checkpoint-interval",type=int)
    q=sp.add_parser("phase-add"); q.add_argument("title"); q.add_argument("objective"); q.add_argument("--owner",default="Main"); q.add_argument("--depends",action="append",default=[]); q.add_argument("--accept",action="append",default=[])
    q=sp.add_parser("plan-approve"); q.add_argument("--by",default="human")
    q=sp.add_parser("dic-create"); q.add_argument("phase_id"); q.add_argument("--constraint",action="append",default=[]); q.add_argument("--evidence",action="append",default=[])
    q=sp.add_parser("dic-view-add"); q.add_argument("phase_id"); q.add_argument("name"); q.add_argument("content"); q.add_argument("--required",action="store_true")
    q=sp.add_parser("eps-generate"); q.add_argument("phase_id"); q.add_argument("actions_json")
    q=sp.add_parser("lane-set"); q.add_argument("phase_id"); q.add_argument("lane",choices=LANE_NAMES); q.add_argument("mode",choices=LANE_MODES)
    q=sp.add_parser("lane-materialize"); q.add_argument("phase_id"); q.add_argument("lane",choices=LANE_NAMES)
    q=sp.add_parser("phase-start"); q.add_argument("phase_id")
    q=sp.add_parser("phase-complete"); q.add_argument("phase_id"); q.add_argument("--evidence",action="append",default=[])
    q=sp.add_parser("verify"); q.add_argument("phase_id"); q.add_argument("outcome",choices=VERIFICATION_OUTCOMES); q.add_argument("rationale"); q.add_argument("--independent",action="store_true")
    q=sp.add_parser("escalate"); q.add_argument("kind",choices=sorted(MATERIAL_ESCALATION_KINDS)); q.add_argument("reason"); q.add_argument("--phase-id")
    q=sp.add_parser("checkpoint-resolve"); q.add_argument("checkpoint_id"); q.add_argument("--decision",choices=("continue","replan","stop"),default="continue"); q.add_argument("--notes",default="")
    q=sp.add_parser("lineage"); q.add_argument("phase_id")
    q=sp.add_parser("prompt"); q.add_argument("role"); q.add_argument("phase_id")
    return p

def main(argv: Sequence[str] | None=None) -> int:
    args=build_parser().parse_args(argv); s=WorkflowStore(args.root)
    try:
        if args.cmd=="init": out=s.init(args.checkpoint_interval,args.force)
        elif args.cmd=="status": out=s.status()
        elif args.cmd=="recover": out=s.recover()
        elif args.cmd=="migrate": out=s.migrate_legacy()
        elif args.cmd=="plan-create": out={"plan_id":s.create_plan(args.title,args.goal,checkpoint_interval=args.checkpoint_interval)}
        elif args.cmd=="phase-add": out={"phase_id":s.add_phase(args.title,args.objective,owner=args.owner,dependencies=args.depends,acceptance=args.accept)}
        elif args.cmd=="plan-approve": s.approve_plan(approved_by=args.by); out={"ok":True}
        elif args.cmd=="dic-create": out={"dic_id":s.create_dic(args.phase_id,constraints=args.constraint,evidence_requirements=args.evidence)}
        elif args.cmd=="dic-view-add": out={"path":s.add_dic_view(args.phase_id,args.name,args.content,required=args.required)}
        elif args.cmd=="eps-generate": out={"eps_id":s.generate_eps(args.phase_id,_read_json_arg(args.actions_json))}
        elif args.cmd=="lane-set": s.set_lane(args.phase_id,args.lane,args.mode); out={"ok":True}
        elif args.cmd=="lane-materialize": out={"path":s.materialize_lane(args.phase_id,args.lane)}
        elif args.cmd=="phase-start": s.start_phase(args.phase_id); out={"ok":True}
        elif args.cmd=="phase-complete": out=s.complete_phase(args.phase_id,evidence=args.evidence)
        elif args.cmd=="verify": s.verify(args.phase_id,args.outcome,rationale=args.rationale,independent=args.independent); out={"ok":True}
        elif args.cmd=="escalate": out={"escalation_id":s.escalate(args.kind,args.reason,phase_id=args.phase_id)}
        elif args.cmd=="checkpoint-resolve": s.resolve_checkpoint(args.checkpoint_id,decision=args.decision,notes=args.notes); out={"ok":True}
        elif args.cmd=="lineage": out=s.lineage(args.phase_id)
        elif args.cmd=="prompt": print(s.render_prompt(args.role,args.phase_id)); return 0
        else: raise WorkflowError("unknown command")
        print(json.dumps(out,indent=2,ensure_ascii=False)); return 0
    except (WorkflowError,MaterialEscalationRequired) as exc:
        print(json.dumps({"ok":False,"error":str(exc)},ensure_ascii=False),file=sys.stderr); return 2

if __name__=="__main__": raise SystemExit(main())
