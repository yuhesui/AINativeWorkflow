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

- MLGym commit `9d40c1b5035202018cd7091fb4e83a9c68b377c0`.
- Qualified WSL CUDA stack is frozen in `requirements.lock.txt`: Python 3.12,
  JAX/JAXlib/CUDA plugin 0.4.38, Flax 0.10.4, Optax 0.2.4,
  TensorFlow Probability 0.25.0, and Gymnax 0.0.9.
- `XLA_PYTHON_CLIENT_PREALLOCATE=false` is required on the 6 GiB GPU.
- Current latest packages (JAX 0.11.1/Flax 0.12.9) are incompatible with the
  frozen task because TensorFlow Probability imports removed JAX internals.
