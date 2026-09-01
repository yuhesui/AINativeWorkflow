"""Durable hierarchy and evidence store for AI-Native Workflow.

The implementation is deliberately small and inspectable.  It is a reference
state machine, not a production concurrency service.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

SCHEMA_VERSION = "5.6.36"
CORE_DIC_VIEWS = ("README.md", "REQUESTS.md", "PLAN.md")
VERIFICATION_OUTCOMES = {"accept", "repair", "replan", "escalate"}


class WorkflowError(RuntimeError):
    """Raised when a requested workflow transition violates the contract."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _assert_id(value: str, label: str) -> None:
    if not value or value.strip() != value:
        raise WorkflowError(f"{label} must be a non-empty trimmed string")
    if any(part in value for part in ("/", "\\", "..")):
        raise WorkflowError(f"unsafe {label}: {value!r}")


def _topological_cycle(nodes: Mapping[str, Mapping[str, Any]]) -> list[str] | None:
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []

    def visit(node_id: str) -> list[str] | None:
        if node_id in visiting:
            try:
                start = stack.index(node_id)
            except ValueError:
                start = 0
            return stack[start:] + [node_id]
        if node_id in visited:
            return None
        visiting.add(node_id)
        stack.append(node_id)
        for dep in nodes[node_id].get("depends_on", []):
            if dep not in nodes:
                raise WorkflowError(f"node {node_id!r} depends on missing node {dep!r}")
            cycle = visit(dep)
            if cycle:
                return cycle
        stack.pop()
        visiting.remove(node_id)
        visited.add(node_id)
        return None

    for node_id in nodes:
        cycle = visit(node_id)
        if cycle:
            return cycle
    return None


class WorkflowStore:
    """Read/write the package-local workflow state and evidence lineage."""

    def __init__(self, repository_root: str | os.PathLike[str]) -> None:
        self.root = Path(repository_root).resolve()
        self.workflow_root = self.root / ".ai-workflow"
        self.state_path = self.workflow_root / "STATE.json"
        self.runtime_dir = self.workflow_root / "runtime"

    def initialize(self, *, project_name: str = "Project", overwrite: bool = False) -> dict[str, Any]:
        self.workflow_root.mkdir(parents=True, exist_ok=True)
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        if self.state_path.exists() and not overwrite:
            return self.load()
        now = _now()
        state = {
            "schema_version": SCHEMA_VERSION,
            "project_name": project_name,
            "created_at": now,
            "updated_at": now,
            "active_plan_id": None,
            "plans": {},
        }
        self._save(state)
        return deepcopy(state)

    def load(self) -> dict[str, Any]:
        if not self.state_path.exists():
            raise WorkflowError(f"state file not found: {self.state_path}")
        try:
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise WorkflowError(f"cannot read state: {exc}") from exc

    def _save(self, state: dict[str, Any]) -> None:
        state["updated_at"] = _now()
        self.workflow_root.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(prefix="STATE.", suffix=".json", dir=self.workflow_root)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(state, handle, indent=2, sort_keys=True, ensure_ascii=False)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, self.state_path)
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)

    def create_plan(self, plan_id: str, *, title: str, goal: str) -> dict[str, Any]:
        _assert_id(plan_id, "plan_id")
        state = self.load()
        if plan_id in state["plans"]:
            raise WorkflowError(f"plan already exists: {plan_id}")
        now = _now()
        state["plans"][plan_id] = {
            "id": plan_id,
            "title": title,
            "goal": goal,
            "status": "draft",
            "created_at": now,
            "approved_at": None,
            "phases": {},
        }
        state["active_plan_id"] = plan_id
        self._save(state)
        return deepcopy(state["plans"][plan_id])

    def approve_plan(self, plan_id: str) -> None:
        state = self.load()
        plan = self._plan(state, plan_id)
        if not plan["phases"]:
            raise WorkflowError("a Plan must contain at least one Phase before approval")
        plan["status"] = "approved"
        plan["approved_at"] = _now()
        state["active_plan_id"] = plan_id
        self._save(state)

    def create_phase(
        self,
        plan_id: str,
        phase_id: str,
        *,
        title: str,
        depends_on: Iterable[str] = (),
    ) -> dict[str, Any]:
        _assert_id(phase_id, "phase_id")
        state = self.load()
        plan = self._plan(state, plan_id)
        if phase_id in plan["phases"]:
            raise WorkflowError(f"phase already exists: {phase_id}")
        dependencies = list(depends_on)
        for dep in dependencies:
            if dep not in plan["phases"]:
                raise WorkflowError(f"missing Phase dependency: {dep}")
        phase = {
            "id": phase_id,
            "title": title,
            "status": "planned",
            "depends_on": dependencies,
            "created_at": _now(),
            "dic": None,
            "eps_attempts": {},
            "actions": {},
            "verifications": [],
        }
        plan["phases"][phase_id] = phase
        self._save(state)
        return deepcopy(phase)

    def create_dic(
        self,
        plan_id: str,
        phase_id: str,
        *,
        dic_id: str,
        views: Mapping[str, str],
        plan_nodes: Mapping[str, Mapping[str, Any]],
        revision: int = 1,
    ) -> dict[str, Any]:
        _assert_id(dic_id, "dic_id")
        state = self.load()
        phase = self._phase(state, plan_id, phase_id)
        if phase["dic"] is not None:
            raise WorkflowError("each Phase may have exactly one DIC package")
        missing = [name for name in CORE_DIC_VIEWS if name not in views]
        if missing:
            raise WorkflowError(f"missing Core DIC views: {', '.join(missing)}")
        normalized_nodes: dict[str, dict[str, Any]] = {}
        for node_id, node in plan_nodes.items():
            _assert_id(node_id, "plan_node_id")
            normalized_nodes[node_id] = {
                "id": node_id,
                "title": str(node.get("title", node_id)),
                "depends_on": list(node.get("depends_on", [])),
                "parallel_group": node.get("parallel_group"),
                "subagent": bool(node.get("subagent", False)),
                "reads": list(node.get("reads", [])),
                "writes": list(node.get("writes", [])),
                "merge_node": bool(node.get("merge_node", False)),
                "evidence_target": node.get("evidence_target"),
            }
        cycle = _topological_cycle(normalized_nodes)
        if cycle:
            raise WorkflowError(f"DIC plan graph contains a cycle: {' -> '.join(cycle)}")

        phase_dir = self.root / "phases" / phase_id / "DIC"
        phase_dir.mkdir(parents=True, exist_ok=True)
        view_paths: dict[str, str] = {}
        for name, content in views.items():
            safe_name = Path(name).name
            if safe_name != name or not safe_name.endswith(".md"):
                raise WorkflowError(f"unsafe or unsupported DIC view name: {name!r}")
            path = phase_dir / safe_name
            path.write_text(content.rstrip() + "\n", encoding="utf-8")
            view_paths[name] = str(path.relative_to(self.root).as_posix())

        dic = {
            "id": dic_id,
            "revision": revision,
            "created_at": _now(),
            "core_views": list(CORE_DIC_VIEWS),
            "views": view_paths,
            "plan_nodes": normalized_nodes,
        }
        dic["contract_hash"] = _json_hash({"views": views, "plan_nodes": normalized_nodes})
        phase["dic"] = dic
        phase["status"] = "ready"
        self._save(state)
        return deepcopy(dic)

    def create_eps(
        self,
        plan_id: str,
        phase_id: str,
        *,
        eps_id: str,
        plan_node_ids: Iterable[str],
        nodes: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        _assert_id(eps_id, "eps_id")
        state = self.load()
        plan = self._plan(state, plan_id)
        if plan["status"] != "approved":
            raise WorkflowError("Plan must be approved before an EPS is created")
        phase = self._phase(state, plan_id, phase_id)
        if phase["dic"] is None:
            raise WorkflowError("Phase must have a DIC before an EPS is created")
        if eps_id in phase["eps_attempts"]:
            raise WorkflowError(f"EPS already exists: {eps_id}")
        selected = list(plan_node_ids)
        for node_id in selected:
            if node_id not in phase["dic"]["plan_nodes"]:
                raise WorkflowError(f"EPS references unknown DIC plan node: {node_id}")
        attempt = len(phase["eps_attempts"]) + 1
        eps_nodes = {}
        for node_id in selected:
            supplied = dict((nodes or {}).get(node_id, {}))
            eps_nodes[node_id] = {
                "plan_node_id": node_id,
                "depends_on": list(supplied.get("depends_on", phase["dic"]["plan_nodes"][node_id]["depends_on"])),
                "parallel_group": supplied.get("parallel_group", phase["dic"]["plan_nodes"][node_id].get("parallel_group")),
                "subagent": bool(supplied.get("subagent", phase["dic"]["plan_nodes"][node_id].get("subagent", False))),
                "executor": supplied.get("executor", "orchestrator"),
                "execution_kind": supplied.get("execution_kind", "model"),
                "model_profile": supplied.get("model_profile"),
                "surface": supplied.get("surface"),
                "prompt_guides": list(supplied.get("prompt_guides", [])),
                "prompt_tuned": bool(supplied.get("prompt_tuned", False)),
                "primary_outcome": supplied.get(
                    "primary_outcome",
                    phase["dic"]["plan_nodes"][node_id].get("title", node_id),
                ),
                "work_packages": list(supplied.get("work_packages", [])),
                "prompt_path": supplied.get("prompt_path"),
                "status": "planned",
            }
        eps = {
            "id": eps_id,
            "attempt": attempt,
            "dic_id": phase["dic"]["id"],
            "dic_hash": phase["dic"]["contract_hash"],
            "created_at": _now(),
            "status": "active",
            "plan_node_ids": selected,
            "nodes": eps_nodes,
        }
        phase["eps_attempts"][eps_id] = eps
        phase["status"] = "active"
        self._save(state)
        return deepcopy(eps)

    def record_action(
        self,
        plan_id: str,
        phase_id: str,
        *,
        action_id: str,
        eps_id: str,
        prompt_node_id: str,
        result: str,
        evidence_paths: Iterable[str] = (),
        status: str = "completed",
        input_versions: Mapping[str, str] | None = None,
        output_versions: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        _assert_id(action_id, "action_id")
        state = self.load()
        phase = self._phase(state, plan_id, phase_id)
        if action_id in phase["actions"]:
            raise WorkflowError(f"Action already exists: {action_id}")
        if eps_id not in phase["eps_attempts"]:
            raise WorkflowError(f"unknown EPS: {eps_id}")
        eps = phase["eps_attempts"][eps_id]
        if prompt_node_id not in eps["nodes"]:
            raise WorkflowError(f"prompt node is not in EPS: {prompt_node_id}")
        runtime_node = eps["nodes"][prompt_node_id]
        if runtime_node.get("execution_kind", "model") == "model":
            if not runtime_node.get("prompt_tuned"):
                raise WorkflowError(
                    f"model-executed EPS node {prompt_node_id!r} cannot run before model/surface prompt tuning"
                )
            if not runtime_node.get("model_profile") or not runtime_node.get("surface"):
                raise WorkflowError(
                    f"model-executed EPS node {prompt_node_id!r} must record model_profile and surface"
                )
            guides = runtime_node.get("prompt_guides", [])
            if not guides or not any("PROMPTING_CORE" in str(item).upper() for item in guides):
                raise WorkflowError(
                    f"model-executed EPS node {prompt_node_id!r} must record PROMPTING_CORE in prompt_guides"
                )
        evidence = list(evidence_paths)
        action = {
            "id": action_id,
            "created_at": _now(),
            "eps_id": eps_id,
            "dic_id": eps["dic_id"],
            "phase_id": phase_id,
            "plan_id": plan_id,
            "prompt_node_id": prompt_node_id,
            "status": status,
            "result": result,
            "evidence_paths": evidence,
            "input_versions": dict(input_versions or {}),
            "output_versions": dict(output_versions or {}),
        }
        phase["actions"][action_id] = action
        eps["nodes"][prompt_node_id]["status"] = status
        if all(node["status"] in {"completed", "integrated", "verified", "retained"} for node in eps["nodes"].values()):
            eps["status"] = "completed"
        self._save(state)
        return deepcopy(action)

    def record_verification(
        self,
        plan_id: str,
        phase_id: str,
        *,
        outcome: str,
        evidence_paths: Iterable[str] = (),
        finding: str = "",
    ) -> dict[str, Any]:
        if outcome not in VERIFICATION_OUTCOMES:
            raise WorkflowError(f"invalid verification outcome: {outcome}")
        state = self.load()
        phase = self._phase(state, plan_id, phase_id)
        record = {
            "id": f"V{len(phase['verifications']) + 1:03d}",
            "created_at": _now(),
            "outcome": outcome,
            "evidence_paths": list(evidence_paths),
            "finding": finding,
        }
        phase["verifications"].append(record)
        phase["status"] = {
            "accept": "accepted",
            "repair": "repair",
            "replan": "replan_required",
            "escalate": "escalated",
        }[outcome]
        self._save(state)
        return deepcopy(record)

    def complete_phase(self, plan_id: str, phase_id: str) -> None:
        state = self.load()
        phase = self._phase(state, plan_id, phase_id)
        if not phase["verifications"] or phase["verifications"][-1]["outcome"] != "accept":
            raise WorkflowError("Phase can complete only after the latest verification outcome is accept")
        phase["status"] = "complete"
        self._save(state)

    def status(self) -> dict[str, Any]:
        state = self.load()
        plan_id = state.get("active_plan_id")
        if not plan_id:
            return {"schema_version": state.get("schema_version"), "active_plan_id": None, "plans": len(state.get("plans", {}))}
        plan = state["plans"][plan_id]
        phases = plan["phases"]
        return {
            "schema_version": state.get("schema_version"),
            "active_plan_id": plan_id,
            "plan_status": plan["status"],
            "phase_count": len(phases),
            "phases": {
                pid: {
                    "status": phase["status"],
                    "dic": phase["dic"]["id"] if phase["dic"] else None,
                    "eps_attempts": len(phase["eps_attempts"]),
                    "actions": len(phase["actions"]),
                    "latest_verification": phase["verifications"][-1]["outcome"] if phase["verifications"] else None,
                }
                for pid, phase in phases.items()
            },
        }

    def recover(self) -> dict[str, Any]:
        errors: list[str] = []
        warnings: list[str] = []
        try:
            state = self.load()
        except WorkflowError as exc:
            return {"ok": False, "schema_version": None, "errors": [str(exc)], "warnings": []}

        if state.get("schema_version") != SCHEMA_VERSION:
            warnings.append(f"state schema is {state.get('schema_version')!r}; runtime expects {SCHEMA_VERSION!r}")
        plans = state.get("plans")
        if not isinstance(plans, dict):
            errors.append("plans must be an object")
            plans = {}

        for plan_id, plan in plans.items():
            phases = plan.get("phases", {})
            phase_nodes = {pid: {"depends_on": p.get("depends_on", [])} for pid, p in phases.items()}
            try:
                cycle = _topological_cycle(phase_nodes)
                if cycle:
                    errors.append(f"Plan {plan_id}: Phase cycle {' -> '.join(cycle)}")
            except WorkflowError as exc:
                errors.append(f"Plan {plan_id}: {exc}")

            for phase_id, phase in phases.items():
                dic = phase.get("dic")
                if dic is None:
                    if phase.get("status") not in {"planned"}:
                        errors.append(f"{plan_id}/{phase_id}: active Phase lacks a DIC")
                    continue
                views = dic.get("views", {})
                for name in CORE_DIC_VIEWS:
                    rel = views.get(name)
                    if not rel:
                        errors.append(f"{plan_id}/{phase_id}: missing Core DIC view {name}")
                    elif not (self.root / rel).is_file():
                        errors.append(f"{plan_id}/{phase_id}: DIC view file not found: {rel}")
                plan_nodes = dic.get("plan_nodes", {})
                try:
                    cycle = _topological_cycle(plan_nodes)
                    if cycle:
                        errors.append(f"{plan_id}/{phase_id}: DIC cycle {' -> '.join(cycle)}")
                except WorkflowError as exc:
                    errors.append(f"{plan_id}/{phase_id}: {exc}")
                for eps_id, eps in phase.get("eps_attempts", {}).items():
                    if eps.get("dic_id") != dic.get("id"):
                        errors.append(f"{plan_id}/{phase_id}/{eps_id}: EPS-DIC ID mismatch")
                    if eps.get("dic_hash") != dic.get("contract_hash"):
                        errors.append(f"{plan_id}/{phase_id}/{eps_id}: EPS-DIC hash mismatch")
                    for node_id in eps.get("plan_node_ids", []):
                        if node_id not in plan_nodes:
                            errors.append(f"{plan_id}/{phase_id}/{eps_id}: unknown plan node {node_id}")
                    for node_id, runtime_node in eps.get("nodes", {}).items():
                        if runtime_node.get("execution_kind", "model") == "model" and runtime_node.get("status") in {
                            "completed",
                            "integrated",
                            "verified",
                            "retained",
                        }:
                            if not runtime_node.get("prompt_tuned"):
                                errors.append(
                                    f"{plan_id}/{phase_id}/{eps_id}/{node_id}: completed model node lacks prompt tuning"
                                )
                            if not runtime_node.get("model_profile") or not runtime_node.get("surface"):
                                errors.append(
                                    f"{plan_id}/{phase_id}/{eps_id}/{node_id}: completed model node lacks model/surface"
                                )
                for action_id, action in phase.get("actions", {}).items():
                    eps_id = action.get("eps_id")
                    if eps_id not in phase.get("eps_attempts", {}):
                        errors.append(f"{plan_id}/{phase_id}/{action_id}: action references missing EPS {eps_id}")
                    for rel in action.get("evidence_paths", []):
                        if rel and not (self.root / rel).exists():
                            warnings.append(f"{plan_id}/{phase_id}/{action_id}: evidence path absent: {rel}")

        active = state.get("active_plan_id")
        if active is not None and active not in plans:
            errors.append(f"active_plan_id references missing Plan: {active}")
        return {
            "ok": not errors,
            "schema_version": state.get("schema_version"),
            "errors": errors,
            "warnings": warnings,
            "plan_count": len(plans),
        }

    @staticmethod
    def _plan(state: dict[str, Any], plan_id: str) -> dict[str, Any]:
        try:
            return state["plans"][plan_id]
        except KeyError as exc:
            raise WorkflowError(f"unknown Plan: {plan_id}") from exc

    @classmethod
    def _phase(cls, state: dict[str, Any], plan_id: str, phase_id: str) -> dict[str, Any]:
        plan = cls._plan(state, plan_id)
        try:
            return plan["phases"][phase_id]
        except KeyError as exc:
            raise WorkflowError(f"unknown Phase: {plan_id}/{phase_id}") from exc
