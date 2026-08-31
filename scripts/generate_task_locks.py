#!/usr/bin/env python3
"""Generate capsule source records and deterministic surface locks."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from eval_common import file_sha256, files, load_json, tree_sha256

ROOT = Path(__file__).resolve().parents[1]

TASKS = {
    "T01": {
        "folder": "T01_query_optimize",
        "benchmark": "Terminal-Bench",
        "identity": "query-optimize",
        "upstream": [
            {
                "kind": "git",
                "url": "https://github.com/harbor-framework/terminal-bench.git",
                "commit": "624df069c505c5ddd21d2d78467dd5579020db95",
                "commit_date": "2026-08-29T16:27:45-07:00",
                "task_path": "tasks/archive/query-optimize",
                "task_tree_git_sha1": "c04a867b98a03f27199ebd6c40d54a2f97d807ae",
            },
            {
                "kind": "Harbor OCI task",
                "registry": "terminal-bench",
                "name": "query-optimize",
                "content_digest": "sha256:169496ea6843cb403b0860132675baf7aa0df0ac8b86221068e27d86395260f4",
                "harbor_version_used": "0.22.0",
            },
            {
                "kind": "dataset asset",
                "url": "https://huggingface.co/datasets/pimpalgaonkar/terminalbench-sqlite-db/resolve/84e42d43436afd2c21b4d3f94c05383fd3a6f78e/oewn.sqlite",
                "revision": "84e42d43436afd2c21b4d3f94c05383fd3a6f78e",
                "sha256": "89eab7555b6b86a74b8e0ee5a7db7beec0b2575a45cd2b22fe132eae79f5ad5a",
                "bytes": 50606080,
            },
        ],
        "license": "See upstream task/repository notices; OEWN database license provenance is retained by the authoritative dataset source.",
        "adaptations": ["pre-fetched the immutable OEWN SQLite asset", "moved official tests/golden/solution to private_eval", "added a semantic-gated continuous transform while retaining native verifier output"],
    },
    "T02": {
        "folder": "T02_dag_execution",
        "benchmark": "SlopCodeBench",
        "identity": "gabeorlanski/dag_execution",
        "upstream": [{"kind": "Harbor OCI task", "registry": "slop-code-bench", "name": "gabeorlanski/dag_execution", "content_digest": "sha256:39aaaeea8576649f6defa53584f234d4873f2cdb8eea806123279909b57ff36c", "embedded_source_revision": "4d38d30-dirty", "task_revision": "v5", "harbor_version_used": "0.22.0"}],
        "license": "No standalone license was distributed in the official task payload; retain upstream notices and restrict this internal copy to evaluation.",
        "adaptations": ["isolated all tests/solutions and checkpoints 2–3", "checkpoint 1 is the sole initial prompt", "later prompts are revealed only after accepted cumulative grading"],
    },
    "T03": {
        "folder": "T03_database_migration",
        "benchmark": "SlopCodeBench",
        "identity": "gabeorlanski/database_migration",
        "upstream": [{"kind": "Harbor OCI task", "registry": "slop-code-bench", "name": "gabeorlanski/database_migration", "content_digest": "sha256:15a6ac32fc6e2ac000df7e634d6f21899aed228418fdb277725ee93790f0d25f", "embedded_source_revision": "4d38d30-dirty", "task_revision": "v5", "harbor_version_used": "0.22.0"}],
        "license": "No standalone license was distributed in the official task payload; retain upstream notices and restrict this internal copy to evaluation.",
        "adaptations": ["isolated all tests/solutions and checkpoints 2–5", "checkpoint 1 is the sole initial prompt", "added frozen state-loss gate after accepted checkpoint 3 and before checkpoint 4 reveal"],
    },
    "T04": {
        "folder": "T04_recli",
        "benchmark": "SlopCodeBench",
        "identity": "gabeorlanski/recli",
        "upstream": [{"kind": "Harbor OCI task", "registry": "slop-code-bench", "name": "gabeorlanski/recli", "content_digest": "sha256:5bbf98e020437d0dac4b74b5da803d4e0c6827540dca31ef26535f7e98209322", "embedded_source_revision": "4d38d30-dirty", "task_revision": "v5", "harbor_version_used": "0.22.0"}],
        "license": "No standalone license was distributed in the official task payload; retain upstream notices and restrict this internal copy to evaluation.",
        "adaptations": ["isolated all tests/solutions and checkpoints 2–8", "checkpoint 1 is the sole initial prompt", "added frozen state-loss gate after accepted checkpoint 4 and before checkpoint 5 reveal"],
    },
    "T05": {
        "folder": "T05_rlMetaMazeMisc",
        "benchmark": "MLGym",
        "identity": "rlMetaMazeMisc",
        "upstream": [{"kind": "git", "url": "https://github.com/facebookresearch/MLGym.git", "commit": "9d40c1b5035202018cd7091fb4e83a9c68b377c0", "commit_date": "2025-08-10T12:47:54-07:00", "authoritative_config": "configs/tasks/rlMetaMaze.yaml"}],
        "license": "MIT (MLGym LICENSE retained).",
        "adaptations": ["excluded unrelated historical benchmark trajectories whose path lengths are not Windows-compatible", "copied target starter and read-only evaluator into test_repo", "kept native five-checkpoint held-out mean reward metric", "added the frozen non-prescriptive research-report requirement"],
    },
    "T06": {
        "folder": "T06_corebench_4252248",
        "benchmark": "CORE-Bench Hard",
        "identity": "capsule-4252248",
        "upstream": [
            {"kind": "git", "url": "https://github.com/siegelz/core-bench.git", "commit": "e32a2980e72fe6eb04ee04eb749458f570625663", "commit_date": "2025-11-23T12:05:05-05:00"},
            {"kind": "Code Ocean capsule", "url": "https://corebench.cs.princeton.edu/capsules/capsule-4252248.tar.gz", "capsule_url": "https://codeocean.com/capsule/4252248/tree/v1", "revision": "v1", "sha256": "bd7a853f2f4859431848c52fcb9288edfbacac41e1b8b8fabc02179989471dd4", "bytes": 18735033},
        ],
        "license": "CORE-Bench MIT license plus licenses retained inside capsule code/data.",
        "adaptations": ["placed the complete capsule in test_repo", "isolated benchmark expected answer and harness", "added official public source-paper citation and CC BY supplementary materials"],
    },
    "T07": {
        "folder": "T07_sequential_neural_score_estimation",
        "benchmark": "PaperBench",
        "identity": "sequential-neural-score-estimation",
        "upstream": [{"kind": "git+LFS", "url": "https://github.com/openai/frontier-evals.git", "commit": "51052cede8cc608f95bb00346635e03759013e5a", "commit_date": "2026-04-21T16:53:31-04:00", "task_path": "project/paperbench/data/papers/sequential-neural-score-estimation", "paper_pdf_lfs_oid_sha256": "4161e45352ce3a8a247dce0841c2a90f0445653872b9616ca1954ebfaa81a57c"}],
        "license": "MIT (frontier-evals/PaperBench license retained); paper copyright remains with its authors/publisher.",
        "adaptations": ["hydrated the exact target Git LFS objects", "preserved project/paperbench plus its required project/common sibling at the pinned revision", "copied the official paper/addendum/blacklist/assets into test_repo", "isolated rubric and judge", "created an empty submission surface without a reference implementation"],
    },
}


def surface(root: Path) -> dict:
    paths = list(files(root))
    return {
        "tree_sha256": tree_sha256(root),
        "file_count": len(paths),
        "bytes": sum(p.stat().st_size for p in paths),
    }


def main() -> int:
    aggregate: dict[str, object] = {
        "schema_version": 1,
        "generated_utc_date": date.today().isoformat(),
        "frozen_task_ids": list(TASKS),
        "tasks": {},
    }
    statuses: list[str] = []
    for task_id, config in TASKS.items():
        task_root = ROOT / "tasks" / config["folder"]
        qualification_status_path = task_root / "qualification" / "QUALIFICATION_STATUS.json"
        qualification = load_json(qualification_status_path) if qualification_status_path.is_file() else {"status": "PENDING"}
        statuses.append(str(qualification["status"]))
        source = {
            "schema_version": 1,
            "task_id": task_id,
            "benchmark": config["benchmark"],
            "frozen_identity": config["identity"],
            "retrieved_utc_date": "2026-08-31",
            "authoritative_sources": config["upstream"],
            "license": config["license"],
            "technical_adaptations": config["adaptations"],
            "visibility": {
                "original_task": "provenance only; never scored workspace",
                "test_repo": "complete agent-facing workspace",
                "private_eval": "physically excluded from agent workspace",
                "reference_manifest": "reference_material/VISIBILITY_MANIFEST.json",
            },
        }
        (task_root / "TASK_SOURCE.json").write_text(json.dumps(source, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        lock = {
            "schema_version": 1,
            "task_id": task_id,
            "benchmark": config["benchmark"],
            "frozen_identity": config["identity"],
            "qualification": qualification,
            "sources": config["upstream"],
            "surfaces": {
                "original_task": surface(task_root / "original_task"),
                "test_repo": surface(task_root / "test_repo"),
                "reference_agent_visible": surface(task_root / "reference_material" / "agent_visible"),
                "reference_provenance_only": surface(task_root / "reference_material" / "provenance_only"),
                "private_eval": surface(task_root / "qualification" / "private_eval"),
            },
            "runtime_tree_sha256": tree_sha256(task_root / "test_repo" / ".ai-workflow"),
            "task_prompt_sha256": file_sha256(task_root / "test_repo" / "TASK.md"),
            "resource_policy_sha256": file_sha256(task_root / "test_repo" / "RESOURCE_POLICY.md"),
            "visibility_manifest_sha256": file_sha256(task_root / "reference_material" / "VISIBILITY_MANIFEST.json"),
        }
        (task_root / "TASK_LOCK.json").write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        aggregate["tasks"][task_id] = {
            "folder": config["folder"],
            "identity": config["identity"],
            "qualification_status": qualification["status"],
            "task_lock_sha256": file_sha256(task_root / "TASK_LOCK.json"),
            "test_repo_tree_sha256": lock["surfaces"]["test_repo"]["tree_sha256"],
            "original_task_tree_sha256": lock["surfaces"]["original_task"]["tree_sha256"],
            "runtime_tree_sha256": lock["runtime_tree_sha256"],
        }
    aggregate["status"] = "READY" if all(s == "QUALIFIED" for s in statuses) else "QUALIFIED_WITH_BLOCKERS" if all(s in {"QUALIFIED", "BLOCKED"} for s in statuses) else "PENDING_QUALIFICATION"
    (ROOT / "manifests" / "TASK_LOCK.json").write_text(json.dumps(aggregate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": aggregate["status"], "tasks": list(TASKS)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
