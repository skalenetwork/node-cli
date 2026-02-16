FROM python:3.13-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml ./

RUN uv pip install --system --no-cache ".[dev]"

FROM python:3.13-slim-bookworm

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    iptables \
    nftables \
    python3-nftables \
    kmod \
    wget \
    binutils && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . .

ENV PYTHONPATH="/app:/usr/lib/python3/dist-packages"
ENV COLUMNS=80
