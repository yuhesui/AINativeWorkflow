# Environment qualification

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

- frontier-evals commit `51052cede8cc608f95bb00346635e03759013e5a` with
  target Git LFS objects hydrated.
- Exact upstream `uv.lock` synced successfully with Python 3.11.15 (202
  packages) in WSL2.
- Paper PDF LFS SHA-256/OID:
  `4161e45352ce3a8a247dce0841c2a90f0445653872b9616ca1954ebfaa81a57c`.
- Docker has no NVIDIA runtime; the available GPU has 6 GiB VRAM.
- Native rubric judging requires an operator-supplied `GRADER_OPENAI_API_KEY`.
