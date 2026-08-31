FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/tmp/agent_home
ENV UV_CACHE_DIR=/tmp/uv-cache
ENV PIP_CACHE_DIR=/tmp/pip-cache
ENV PYTHONUNBUFFERED=1
ENV TERM=xterm
ENV COLUMNS=240
ENV LINES=60

RUN apt-get update  && apt-get install -y --no-install-recommends         build-essential         ca-certificates         curl         git         procps         util-linux         docker-cli  && (apt-get install -y --no-install-recommends docker-compose-plugin         || apt-get install -y --no-install-recommends docker-compose-v2         || apt-get install -y --no-install-recommends docker-compose)  && mkdir -p /usr/local/lib/docker/cli-plugins /usr/lib/docker/cli-plugins  && if [ -x /usr/bin/docker-compose ]; then         ln -sf /usr/bin/docker-compose /usr/local/lib/docker/cli-plugins/docker-compose;         ln -sf /usr/bin/docker-compose /usr/lib/docker/cli-plugins/docker-compose;     fi  && rm -rf /var/lib/apt/lists/*

RUN groupadd -g 1000 agent  && useradd -m -u 1000 -g 1000 -d "$HOME" -s /bin/bash agent  && (getent group docker >/dev/null || groupadd docker)  && usermod -aG docker agent  && mkdir -p /app /assets /workspace "$HOME" "$UV_CACHE_DIR" "$PIP_CACHE_DIR"  && chown -R agent:agent /app /workspace "$HOME" "$UV_CACHE_DIR" "$PIP_CACHE_DIR"  && chmod 1777 /tmp "$UV_CACHE_DIR" "$PIP_CACHE_DIR"

WORKDIR /app
