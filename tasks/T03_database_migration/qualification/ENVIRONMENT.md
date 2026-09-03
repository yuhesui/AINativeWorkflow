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

- Official Harbor 0.22.0 SlopCodeBench task, embedded revision
  `4d38d30-dirty`, task revision `v5`.
- WSL qualification environment uses Python 3.12.3 and pytest 9.0.2.
- The five cumulative checkpoints are private and sequentially revealable.

On 2026-09-04, the upstream environment's moving `npm@latest` installation
resolved to npm 12.0.2, which requires Node 22.22.2 or newer and rejected the
upstream-pinned Node 22.12.0. The scored harness therefore uses
`qualification/environment/Dockerfile`, whose sole dependency change pins npm
10.9.0. The immutable upstream Dockerfile remains in `original_task/`.
