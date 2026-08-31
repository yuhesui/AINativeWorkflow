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

- CORE-Bench commit `e32a2980e72fe6eb04ee04eb749458f570625663`.
- Code Ocean capsule v1 archive SHA-256
  `bd7a853f2f4859431848c52fcb9288edfbacac41e1b8b8fabc02179989471dd4`.
- Official archived image
  `registry.codeocean.com/published/0012b3fb-3cf2-41fa-9b8d-6cc055b53ca2:v1`,
  local digest
  `sha256:cde83cedfb51150e20b442cd2f988f62f92864f8d661979c11f7f035c4b156f5`.
- The capsule is the upstream R 3.4.2 / Ubuntu 16.04 environment.
