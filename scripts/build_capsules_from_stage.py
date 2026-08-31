#!/usr/bin/env python3
"""Mechanically assemble frozen task surfaces from reviewed upstream staging trees.

This script never runs a benchmark agent or a scored trajectory.  It is intentionally
strict about destination paths because it clears only the provenance/evaluator surfaces
that setup owns.  Source acquisition and immutable revisions are recorded in task locks.
"""

from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / ".upstream_stage"
TASKS = ROOT / "tasks"


def _copy_tree(
    src: Path,
    dst: Path,
    *,
    ignore_git: bool = False,
    ignored_names: tuple[str, ...] = (),
) -> None:
    if not src.is_dir():
        raise FileNotFoundError(src)
    patterns = ((".git",) if ignore_git else ()) + ignored_names
    ignore = shutil.ignore_patterns(*patterns) if patterns else None
    shutil.copytree(src, dst, dirs_exist_ok=True, ignore=ignore)


def _copy_file(src: Path, dst: Path) -> None:
    if not src.is_file():
        raise FileNotFoundError(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _clear_owned(path: Path) -> None:
    resolved = path.resolve()
    task_root = TASKS.resolve()
    if task_root not in resolved.parents:
        raise RuntimeError(f"Refusing to clear path outside tasks/: {resolved}")
    allowed_names = {"original_task", "private_eval", "agent_visible", "provenance_only"}
    if resolved.name not in allowed_names:
        raise RuntimeError(f"Refusing to clear non-owned surface: {resolved}")
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def _task(folder: str) -> Path:
    path = TASKS / folder
    if not path.is_dir():
        raise FileNotFoundError(path)
    return path


def build_t1() -> None:
    task = _task("T01_query_optimize")
    original = task / "original_task"
    private = task / "qualification" / "private_eval"
    _clear_owned(original)
    _clear_owned(private)
    _copy_tree(STAGE / "t1" / "query-optimize", original)
    _copy_file(STAGE / "oewn.sqlite", original / "frozen_assets" / "oewn.sqlite")
    _copy_tree(STAGE / "t1" / "query-optimize" / "tests", private / "tests")
    _copy_tree(STAGE / "t1" / "query-optimize" / "solution", private / "solution")
    _copy_file(STAGE / "t1" / "query-optimize" / "task.toml", private / "task.toml")
    _copy_file(STAGE / "oewn.sqlite", task / "test_repo" / "oewn.sqlite")
    _copy_file(
        STAGE / "t1" / "query-optimize" / "environment" / "task-deps" / "my-sql-query.sql",
        task / "test_repo" / "my-sql-query.sql",
    )


def build_slopcode(folder: str, stage_name: str) -> None:
    task = _task(folder)
    src = STAGE / stage_name[0:2] / stage_name
    # Stage directories are t2/t3/t4, not derived from task names.
    stage_map = {
        "dag_execution": STAGE / "t2" / "dag_execution",
        "database_migration": STAGE / "t3" / "database_migration",
        "recli": STAGE / "t4" / "recli",
    }
    src = stage_map[stage_name]
    original = task / "original_task"
    private = task / "qualification" / "private_eval"
    _clear_owned(original)
    _clear_owned(private)
    _copy_tree(src, original)
    _copy_tree(src / "tests", private / "tests")
    _copy_tree(src / "steps", private / "steps")
    _copy_file(src / "task.toml", private / "task.toml")
    if (src / "README.md").exists():
        _copy_file(src / "README.md", private / "UPSTREAM_README.md")


def build_t5() -> None:
    task = _task("T05_rlMetaMazeMisc")
    upstream = STAGE / "mlgym-repo"
    original = task / "original_task"
    private = task / "qualification" / "private_eval"
    _clear_owned(original)
    _clear_owned(private)
    # Upstream's checked-in historical benchmark trajectories are unrelated to
    # rlMetaMazeMisc and contain Windows-incompatible path lengths.  The full
    # framework, target task, evaluator, configs, docs, and licenses are kept.
    _copy_tree(upstream, original, ignore_git=True, ignored_names=("trajectories",))
    _copy_file(upstream / "configs" / "tasks" / "rlMetaMaze.yaml", private / "rlMetaMaze.yaml")
    _copy_file(upstream / "data" / "rlMetaMazeMisc" / "evaluate.py", private / "evaluate.py")
    visible = upstream / "data" / "rlMetaMazeMisc"
    _copy_tree(visible / "src", task / "test_repo" / "src")
    _copy_file(visible / "evaluate.py", task / "test_repo" / "evaluate.py")
    _copy_file(visible / "requirements.txt", task / "test_repo" / "requirements.txt")
    _copy_file(upstream / "configs" / "tasks" / "rlMetaMaze.yaml", task / "test_repo" / "task_config.yaml")
    _copy_file(upstream / "LICENSE", task / "test_repo" / "UPSTREAM_LICENSE")


def build_t6() -> None:
    task = _task("T06_corebench_4252248")
    capsule = STAGE / "t6capsule" / "capsule-4252248"
    harness = STAGE / "core-bench-repo"
    original = task / "original_task"
    private = task / "qualification" / "private_eval"
    _clear_owned(original)
    _clear_owned(private)
    _copy_tree(capsule, original / "capsule-4252248")
    _copy_tree(harness, original / "core-bench-harness", ignore_git=True)
    _copy_file(STAGE / "capsule-4252248.tar.gz", original / "capsule-4252248.tar.gz")
    _copy_tree(harness / "benchmark", private / "benchmark")
    _copy_file(harness / "benchmark_utils" / "capsules.csv", private / "capsules.csv")
    _copy_tree(capsule, task / "test_repo" / "capsule-4252248")


def build_t7() -> None:
    task = _task("T07_sequential_neural_score_estimation")
    project = STAGE / "frontier-evals-repo" / "project" / "paperbench"
    paper = project / "data" / "papers" / "sequential-neural-score-estimation"
    original = task / "original_task"
    private = task / "qualification" / "private_eval"
    agent_ref = task / "reference_material" / "agent_visible"
    provenance_ref = task / "reference_material" / "provenance_only"
    for owned in (original, private, agent_ref, provenance_ref):
        _clear_owned(owned)
    _copy_tree(project, original)
    _copy_tree(project / "paperbench", private / "paperbench")
    _copy_file(project / "pyproject.toml", private / "pyproject.toml")
    _copy_file(project / "uv.lock", private / "uv.lock")
    _copy_file(paper / "rubric.json", private / "rubric.json")
    for name in ("paper.pdf", "paper.md", "addendum.md", "blacklist.txt", "config.yaml"):
        _copy_file(paper / name, agent_ref / name)
    _copy_tree(paper / "assets", agent_ref / "assets")
    for name in ("paper.pdf", "paper.md", "addendum.md", "blacklist.txt"):
        _copy_file(paper / name, task / "test_repo" / "paper" / name)
    _copy_tree(paper / "assets", task / "test_repo" / "paper" / "assets")
    (task / "test_repo" / "submission").mkdir(exist_ok=True)
    _copy_file(project / "LICENSE", provenance_ref / "LICENSE") if (project / "LICENSE").exists() else None


def main() -> None:
    build_t1()
    build_slopcode("T02_dag_execution", "dag_execution")
    build_slopcode("T03_database_migration", "database_migration")
    build_slopcode("T04_recli", "recli")
    build_t5()
    build_t6()
    build_t7()
    print("Built T01-T07 capsule surfaces from reviewed staging snapshots.")


if __name__ == "__main__":
    main()
