"""Deterministic repair-to-accept demonstration."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from .impact import dependency_impact_cone
from .store import WorkflowStore


def _write_evidence(root: Path, name: str, payload: str) -> str:
    path = root / ".ai-workflow" / "runtime" / "evidence" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload.rstrip() + "\n", encoding="utf-8")
    return str(path.relative_to(root).as_posix())


def run_demo(workspace: str | None = None) -> dict[str, Any]:
    temporary = None
    if workspace is None:
        temporary = tempfile.TemporaryDirectory(prefix="ai-workflow-demo-")
        root = Path(temporary.name) / "repo"
    else:
        root = Path(workspace).resolve()
    root.mkdir(parents=True, exist_ok=True)

    store = WorkflowStore(root)
    store.initialize(project_name="Anonymous verification-gated demo", overwrite=True)
    store.create_plan("plan_demo", title="Verification-gated demo", goal="Demonstrate repair to bounded recovery")
    store.create_phase("plan_demo", "phase_demo", title="Deterministic seven-node trace")

    plan_nodes = {
        "collect": {"title": "Collect", "writes": ["raw"]},
        "normalize": {"title": "Normalize", "depends_on": ["collect"], "reads": ["raw"], "writes": ["normalized"]},
        "experiment": {"title": "Experiment", "depends_on": ["normalize"], "reads": ["normalized"], "writes": ["metrics"]},
        "table": {"title": "Table", "depends_on": ["experiment"], "reads": ["metrics"], "writes": ["table"]},
        "paper": {"title": "Paper", "depends_on": ["table"], "reads": ["table"], "writes": ["paper"]},
        "release": {"title": "Release", "depends_on": ["paper"], "reads": ["paper"], "writes": ["release"]},
        "theory": {"title": "Independent theory", "writes": ["theory"], "parallel_group": "independent", "subagent": True},
    }
    views = {
        "README.md": "# Demo Phase\n\nOne durable DIC; verification-triggered repair may create another EPS.",
        "REQUESTS.md": "# Requests\n\n- [ ] Demonstrate repair → accept while retaining unaffected evidence.",
        "PLAN.md": "# Durable execution graph\n\n`collect → normalize → experiment → table → paper → release`; `theory` is independent.",
    }
    dic = store.create_dic("plan_demo", "phase_demo", dic_id="dic_demo", views=views, plan_nodes=plan_nodes)
    store.approve_plan("plan_demo")

    all_nodes = list(plan_nodes)
    deterministic_nodes = {
        node_id: {
            "execution_kind": "deterministic",
            "executor": "python-reference-runtime",
            "surface": "local-cli",
            "model_profile": "deterministic",
            "prompt_guides": ["PROMPTING_CORE.md"],
            "prompt_tuned": True,
            "primary_outcome": plan_nodes[node_id]["title"],
            "work_packages": ["write fixed structural evidence"],
        }
        for node_id in all_nodes
    }
    first = store.create_eps(
        "plan_demo",
        "phase_demo",
        eps_id="eps_001",
        plan_node_ids=all_nodes,
        nodes=deterministic_nodes,
    )
    first_actions: list[str] = []
    for node_id in all_nodes:
        evidence = _write_evidence(root, f"eps_001__{node_id}.txt", f"attempt=1\nnode={node_id}\nstatus=completed")
        action_id = f"a1_{node_id}"
        store.record_action(
            "plan_demo",
            "phase_demo",
            action_id=action_id,
            eps_id=first["id"],
            prompt_node_id=node_id,
            result="completed",
            evidence_paths=[evidence],
            output_versions={key: "v1" for key in plan_nodes[node_id].get("writes", [])},
        )
        first_actions.append(action_id)

    failed_evidence = _write_evidence(root, "verification_001.txt", "normalize schema_version mismatch: expected v2, observed v1")
    store.record_verification(
        "plan_demo",
        "phase_demo",
        outcome="repair",
        evidence_paths=[failed_evidence],
        finding="normalize output has a deterministic schema/version mismatch",
    )

    cone = dependency_impact_cone(plan_nodes, {"normalized"})
    repair_nodes = ["normalize"] + [node for node in ("experiment", "table", "paper", "release") if node in cone]
    second = store.create_eps(
        "plan_demo",
        "phase_demo",
        eps_id="eps_002",
        plan_node_ids=repair_nodes,
        nodes={node_id: deterministic_nodes[node_id] for node_id in repair_nodes},
    )
    second_actions: list[str] = []
    for node_id in repair_nodes:
        evidence = _write_evidence(root, f"eps_002__{node_id}.txt", f"attempt=2\nnode={node_id}\nstatus=completed\nschema=v2")
        action_id = f"a2_{node_id}"
        store.record_action(
            "plan_demo",
            "phase_demo",
            action_id=action_id,
            eps_id=second["id"],
            prompt_node_id=node_id,
            result="completed after bounded repair",
            evidence_paths=[evidence],
            input_versions={"normalized": "v2"} if node_id != "normalize" else {"raw": "v1"},
            output_versions={key: "v2" for key in plan_nodes[node_id].get("writes", [])},
        )
        second_actions.append(action_id)

    accepted_evidence = _write_evidence(root, "verification_002.txt", "re-verification accepted schema v2 and declared downstream outputs")
    store.record_verification(
        "plan_demo",
        "phase_demo",
        outcome="accept",
        evidence_paths=[accepted_evidence],
        finding="bounded repair and downstream re-execution satisfy the DIC",
    )
    store.complete_phase("plan_demo", "phase_demo")

    fresh = WorkflowStore(root)
    recovery = fresh.recover()
    result = {
        "demo": "verification-gated bounded recovery",
        "root": str(root),
        "dic_id": dic["id"],
        "stable_dic_across_attempts": first["dic_id"] == second["dic_id"] == dic["id"],
        "first_eps": {"id": first["id"], "nodes": all_nodes, "actions": first_actions},
        "verification_sequence": ["repair", "accept"],
        "changed_keys": ["normalized"],
        "declared_downstream_impact_cone": sorted(cone),
        "second_eps": {"id": second["id"], "nodes": repair_nodes, "actions": second_actions},
        "retained_nodes": ["collect", "theory"],
        "recovery": recovery,
        "status": fresh.status(),
    }
    if temporary is not None:
        result["temporary_workspace_removed_after_return"] = True
        temporary.cleanup()
    return result


def write_demo(output: str, workspace: str | None = None) -> dict[str, Any]:
    result = run_demo(workspace)
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
