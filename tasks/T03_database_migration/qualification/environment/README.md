# Qualified environment adaptation

This Dockerfile is the scored-environment adaptation of the immutable upstream
`original_task/environment/Dockerfile`.

The only semantic change is replacing the moving `npm@latest` installation with
`npm@10.9.0`, the npm version bundled with the upstream-pinned Node.js 22.12.0.
On 2026-09-03, `npm@latest` resolved to npm 12.0.2, whose engine requirement is
Node.js 22.22.2 or newer, so the upstream environment could no longer build.

The harness hashes this adapted Dockerfile, uses that hash in the Docker image
tag, and records its path and hash in `RUN.json`. The upstream Dockerfile remains
unchanged for provenance.
