#!/usr/bin/env python3
"""Write frozen qualification records from the non-agent setup evidence.

This script does not invoke a benchmark, a model, or a grader.  It only emits
the required audit documents from facts established during 2026-08-31 setup.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

COMMON_ENV = """# Environment qualification

Qualification date: 2026-08-31 (Asia/Shanghai).  All work described here was
non-scored infrastructure validation; no candidate model or scored trajectory
was run.

Host platform:

- Windows 11 host, WSL2 Ubuntu 24.04.3 LTS.
- Windows Python 3.13.2 and WSL Python 3.12.3.
- Docker Engine 29.1.3 and Docker Compose 2.40.3 in WSL2.
- NVIDIA GeForce RTX 4050 Laptop GPU, 6 GiB VRAM, driver 596.58.
- Docker exposes only `runc`/`io.containerd.runc.v2`; NVIDIA Container Toolkit
  is not installed.

The authoritative dependency and image details for this task are below.
"""

TASKS: dict[str, dict[str, object]] = {
    "T01_query_optimize": {
        "status": "QUALIFIED",
        "environment": """
- Harbor 0.22.0 task payload plus SQLite 3 and Python.
- Frozen OEWN database: 50,606,080 bytes, SHA-256
  `89eab7555b6b86a74b8e0ee5a7db7beec0b2575a45cd2b22fe132eae79f5ad5a`.
- The official verifier and the semantic-gated continuous score execute
  locally without network access.
""",
        "leakage": """
The agent repository contains the immutable SQLite database, task prompt, and
an editable `query.sql`.  Official tests, golden query, solution script,
baseline timing lock, and continuous-scoring implementation are physically
outside `test_repo/` under `qualification/private_eval/`.  A recursive
sensitive-name/content scan found no expected-answer or reference-solution
material in the agent workspace.  Direct materialization removes
`.ai-workflow/`; AI-Native materialization retains it.
""",
        "report": """
The exact official task and verifier were frozen.  Seven repeated executions
of the official golden query passed every semantic gate and the native timing
threshold.  The locked unoptimized runtime was 344.385778 seconds and the
golden median was 0.459976 seconds (ratio 748.703146965587).  The continuous
score is gated by exact semantic correctness and retains raw native verifier
output; the accepted oracle score is 100.  Evidence is in
`oracle_runs/oracle_01/GRADER_RAW_7.json` and `private_eval/BASELINE_LOCK.json`.
""",
        "evidence": ["oracle_runs/oracle_01/GRADER_RAW_7.json", "private_eval/BASELINE_LOCK.json"],
        "blockers": [],
    },
    "T02_dag_execution": {
        "status": "QUALIFIED",
        "environment": """
- Official Harbor 0.22.0 SlopCodeBench task, embedded revision
  `4d38d30-dirty`, task revision `v5`.
- WSL qualification environment uses Python 3.12.3 and pytest 9.0.2.
- All three cumulative checkpoint payloads, tests, and solutions are retained
  in private evaluation storage; only checkpoint 1 is initially visible.
""",
        "leakage": """
Every official test, solution, and checkpoints 2-3 prompt is physically
isolated under `qualification/private_eval/`.  `test_repo/` contains only the
greenfield repository, checkpoint-1 instructions, resource policy, and clean
runtime.  `reveal_checkpoint.py` permits only the immediate next checkpoint
after an accepted cumulative grader record.
""",
        "report": """
The official final checkpoint-3 reference implementation ran and parsed: 49
passed, 2 failed; strict pass rate 49/51 (0.960784...), core 3/3, isolated
10/10.  The same two failures (`test_branch_if` and
`test_stderr_validation`) occur in the official checkpoint-1 reference (31
passed, 2 failed), so this is a frozen upstream oracle defect rather than
checkpoint erosion.  No benchmark semantics or grader were changed.  The
environment is qualified with that explicit caveat; raw reports for both
checkpoints are retained under `oracle_runs/`.
""",
        "evidence": ["oracle_runs/checkpoint_1", "oracle_runs/checkpoint_3"],
        "blockers": [],
    },
    "T03_database_migration": {
        "status": "QUALIFIED",
        "environment": """
- Official Harbor 0.22.0 SlopCodeBench task, embedded revision
  `4d38d30-dirty`, task revision `v5`.
- WSL qualification environment uses Python 3.12.3 and pytest 9.0.2.
- The five cumulative checkpoints are private and sequentially revealable.
""",
        "leakage": """
All official tests, solutions, and checkpoints 2-5 are under
`qualification/private_eval/`; none are reachable from `test_repo/`.
Checkpoint revelation, Direct/AI-Native materialization, full-repository
finalization, and the checkpoint-3 state-loss boundary were tested in the
qualification-only `oracle_runs/harness_dry/` tree.
""",
        "report": """
The official checkpoint-5 oracle produced 136 passed and 1 skipped, with core
3/3, isolated 20/20, and strict pass rate 1.0.  A non-scored dry run verified
both condition workspaces, sequential checkpoint reveal, exact state-loss
snapshot after checkpoint 3 and before checkpoint 4, transcript exclusion,
and archival of each entire final repository plus separate result records.
No directory was added to the scored `runs/` or `run_results/` surfaces.
""",
        "evidence": ["oracle_runs/checkpoint_5", "oracle_runs/harness_dry", "oracle_runs/harness_finalizer_v2"],
        "blockers": [],
    },
    "T04_recli": {
        "status": "QUALIFIED",
        "environment": """
- Official Harbor 0.22.0 SlopCodeBench task, embedded revision
  `4d38d30-dirty`, task revision `v5`.
- WSL qualification uses Python 3.12.3, pytest 9.0.2, Docker Engine 29.1.3,
  and Docker Compose 2.40.3.
- The eight cumulative checkpoints are private and sequentially revealable.
""",
        "leakage": """
All official tests, solutions, and checkpoints 2-8 are physically isolated
under `qualification/private_eval/`.  The initial repository exposes only
checkpoint 1 and legitimate project files.  The harness enforces the frozen
state-loss boundary after accepted checkpoint 4 and before checkpoint 5.
""",
        "report": """
The official final checkpoint-8 oracle ran successfully: 255/255 tests passed,
core 7/7, isolated 41/41, strict pass rate 1.0.  Native raw output and parsed
checkpoint metrics are retained under `oracle_runs/checkpoint_8/`.
""",
        "evidence": ["oracle_runs/checkpoint_8"],
        "blockers": [],
    },
    "T05_rlMetaMazeMisc": {
        "status": "BLOCKED",
        "environment": """
- MLGym commit `9d40c1b5035202018cd7091fb4e83a9c68b377c0`.
- Qualified WSL CUDA stack is frozen in `requirements.lock.txt`: Python 3.12,
  JAX/JAXlib/CUDA plugin 0.4.38, Flax 0.10.4, Optax 0.2.4,
  TensorFlow Probability 0.25.0, and Gymnax 0.0.9.
- `XLA_PYTHON_CLIENT_PREALLOCATE=false` is required on the 6 GiB GPU.
- Current latest packages (JAX 0.11.1/Flax 0.12.9) are incompatible with the
  frozen task because TensorFlow Probability imports removed JAX internals.
""",
        "leakage": """
The read-only native evaluator and authoritative config are retained under
private evaluation and duplicated only where the benchmark legitimately makes
evaluation mechanics visible.  No trained reference policy or expected
held-out reward is present in `test_repo/`.  The smoke checkpoint is confined
to `qualification/oracle_runs/baseline_01/`.
""",
        "report": """
The pinned CUDA environment detected the RTX 4050 and completed one full native
PPO training seed, producing `checkpoints/config-42-0.pkl`; a second seed was
intentionally interrupted after 35% because one full seed was sufficient for
expensive non-agent infrastructure validation.  The task is nevertheless
BLOCKED: authoritative `configs/tasks/rlMetaMaze.yaml` specifies 64 evaluation
environments, while the shipped target `evaluate.py` hard-codes batch size 256.
Changing either value would alter the frozen task.  An explicit protocol
revision or authoritative upstream resolution is required before any scored
T5/T5m run.
""",
        "evidence": ["oracle_runs/baseline_01", "requirements.lock.txt", "private_eval/rlMetaMaze.yaml", "private_eval/evaluate.py"],
        "blockers": ["Frozen authoritative config requests 64 evaluation environments but the shipped evaluator hard-codes 256."],
    },
    "T06_corebench_4252248": {
        "status": "QUALIFIED",
        "environment": """
- CORE-Bench commit `e32a2980e72fe6eb04ee04eb749458f570625663`.
- Code Ocean capsule v1 archive SHA-256
  `bd7a853f2f4859431848c52fcb9288edfbacac41e1b8b8fabc02179989471dd4`.
- Official archived image
  `registry.codeocean.com/published/0012b3fb-3cf2-41fa-9b8d-6cc055b53ca2:v1`,
  local digest
  `sha256:cde83cedfb51150e20b442cd2f988f62f92864f8d661979c11f7f035c4b156f5`.
- The capsule is the upstream R 3.4.2 / Ubuntu 16.04 environment.
""",
        "leakage": """
The complete capsule and public paper/supplements are agent-visible under the
official policy.  The expected numerical answer and CORE-Bench harness are
isolated under `qualification/private_eval/`; they are absent from
`test_repo/` and agent-visible references.  The private native wrapper grades
only the submitted answer and is never mounted into a scored workspace.
""",
        "report": """
The official Code Ocean image was restored and all three capsule R scripts ran
successfully (exit 0, approximately 29 seconds).  The generated PDF contained
the exact official result `AUC = 0.4929241`.  The private native single-question
grader returned 1/1 correct.  Raw extracted output, generated artifacts, and
the structured oracle result are retained under `oracle_runs/full_01/`.  A
qualification-only research-task state-loss dry run also verified the 4-hour
half-budget gate, stable-handoff evidence archival, transcript exclusion, and
surviving repository hash.
""",
        "evidence": ["oracle_runs/full_01", "oracle_runs/state_loss_dry", "private_eval/expected_answer.json", "private_eval/grade_answer.py"],
        "blockers": [],
    },
    "T07_sequential_neural_score_estimation": {
        "status": "BLOCKED",
        "environment": """
- frontier-evals commit `51052cede8cc608f95bb00346635e03759013e5a` with
  target Git LFS objects hydrated.
- Exact upstream `uv.lock` synced successfully with Python 3.11.15 (202
  packages) in WSL2.
- Paper PDF LFS SHA-256/OID:
  `4161e45352ce3a8a247dce0841c2a90f0445653872b9616ca1954ebfaa81a57c`.
- Docker has no NVIDIA runtime; the available GPU has 6 GiB VRAM.
- Native rubric judging requires an operator-supplied `GRADER_OPENAI_API_KEY`.
""",
        "leakage": """
The source paper, addendum, blacklist, and officially distributed research
assets are agent-visible.  The complete rubric, native judge code, and any
reference grading material are physically isolated under
`qualification/private_eval/`.  The submission surface contains no reference
implementation.  `original_task/` is provenance-only and is never mounted as
the scored workspace.
""",
        "report": """
The complete PaperBench project was reconstructed with both `project/paperbench`
and its required `project/common` sibling.  Frozen dependency synchronization
succeeded.  An initial unit run produced 38 passed, 14 skipped, 4 failed, and
11 errors: the four failures were exclusively API-key-dependent SimpleJudge
tests and the errors were Docker-socket permission failures in the non-root
WSL invocation.  Both official Dockerfiles then built successfully, and the
root suite passed 49/49 with 18 API-judge cases deselected.  These checks are
recorded in `oracle_runs/`; they establish substantial execution machinery but cannot
qualify the native target grader or full target reproduction.  T7/T7m remain
BLOCKED because no approved grader credential is available and this Docker
installation lacks NVIDIA runtime support; the 6 GiB host GPU also cannot be
assumed sufficient for the frozen full reproduction.  No Code-Dev downgrade
was made.
""",
        "evidence": ["oracle_runs/unit-tests.xml", "oracle_runs/container-build"],
        "blockers": [
            "Native rubric judge cannot be qualified without an operator-supplied GRADER_OPENAI_API_KEY.",
            "Docker has no NVIDIA runtime, and full target GPU feasibility is unqualified on the 6 GiB device.",
        ],
    },
}


def write_text(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def main() -> int:
    for folder, task in TASKS.items():
        q = ROOT / "tasks" / folder / "qualification"
        write_text(q / "ENVIRONMENT.md", COMMON_ENV + str(task["environment"]))
        write_text(q / "LEAKAGE_AUDIT.md", "# Leakage audit\n\n" + str(task["leakage"]))
        status = str(task["status"])
        write_text(
            q / "QUALIFICATION_REPORT.md",
            f"# Qualification report\n\nStatus: **{status}**\n\n" + str(task["report"]),
        )
        record = {
            "schema_version": 1,
            "status": status,
            "qualification_date": "2026-08-31",
            "candidate_agent_used": False,
            "scored_run_created": False,
            "evidence": task["evidence"],
            "blockers": task["blockers"],
        }
        (q / "QUALIFICATION_STATUS.json").write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    environment_lock = {
        "schema_version": 1,
        "frozen_utc_date": "2026-08-31",
        "host": {
            "os": "Windows 11 with WSL2 Ubuntu 24.04.3 LTS",
            "timezone": "Asia/Shanghai",
            "windows_python": "3.13.2",
            "wsl_python": "3.12.3",
            "docker_engine": "29.1.3",
            "docker_compose": "2.40.3",
            "gpu": "NVIDIA GeForce RTX 4050 Laptop GPU",
            "gpu_vram_gib": 6,
            "nvidia_driver": "596.58",
            "docker_runtimes": ["runc", "io.containerd.runc.v2"],
            "nvidia_container_runtime": False,
        },
        "qualified_stacks": {
            "slopcodebench": {"python": "3.12.3", "pytest": "9.0.2"},
            "mlgym": {"python": "3.12.3", "lock_file": "tasks/T05_rlMetaMazeMisc/qualification/requirements.lock.txt", "required_environment": {"XLA_PYTHON_CLIENT_PREALLOCATE": "false"}},
            "paperbench": {"python": "3.11.15", "package_count": 202, "lock_file": "tasks/T07_sequential_neural_score_estimation/original_task/project/paperbench/uv.lock", "pb_env_image_id": "sha256:9b80c1bce02930470851d1ee5ec7b21e5d19f95377913b89dd65d57c992ef956", "pb_reproducer_image_id": "sha256:86f0f081db56e1f10d677bdbda7a73aa4dd052dccb6131bf4d33b7e9a7c1a921"},
            "corebench_image": {"reference": "registry.codeocean.com/published/0012b3fb-3cf2-41fa-9b8d-6cc055b53ca2:v1", "digest": "sha256:cde83cedfb51150e20b442cd2f988f62f92864f8d661979c11f7f035c4b156f5"},
        },
        "network_policy": "No network for T1; package/literature access only where the task resource policy permits it. All scored conditions use the same task-specific policy.",
        "blocked_capabilities": ["PaperBench native API judge credential not supplied", "NVIDIA Docker runtime absent"],
    }
    (ROOT / "manifests" / "ENVIRONMENT_LOCK.json").write_text(
        json.dumps(environment_lock, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({folder: task["status"] for folder, task in TASKS.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
