FROM ubuntu:24.04 AS builder

ARG PYTHON_VERSION=3.13

ENV DEBIAN_FRONTEND=noninteractive
ENV UV_PYTHON_INSTALL_DIR=/opt/python

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml ./

RUN uv python install "$PYTHON_VERSION" && \
    uv venv --python "$PYTHON_VERSION" /opt/venv && \
    uv pip install --python /opt/venv --no-cache ".[dev]"

FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    binutils \
    ca-certificates \
    git \
    iptables \
    kmod \
    nftables \
    patchelf \
    python3-nftables \
    wget && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /opt/python /opt/python
COPY --from=builder /opt/venv /opt/venv

RUN printf '%s\n' '/usr/lib/python3/dist-packages' \
    > /opt/venv/lib/python3.13/site-packages/ubuntu-system-packages.pth

COPY . .

RUN patchelf --remove-needed libSegFault.so datafiles/skaled-ssl-test

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV COLUMNS=80
