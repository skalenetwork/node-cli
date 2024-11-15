FROM python:3.11-bookworm

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
                       git \
                       build-essential \
                       software-properties-common \
                       zlib1g-dev \
                       libssl-dev \
                       libffi-dev \
                       swig \
                       iptables \
                       nftables \ 
                       python3-nftables \ 
                       libxslt-dev \
                       kmod


RUN mkdir /app
WORKDIR /app

COPY . .

ENV PATH=/app/buildvenv/bin:$PATH
ENV PYTHONPATH="{PYTHONPATH}:/usr/lib/python3/dist-packages"

RUN python3.11 -m venv /app/buildvenv && \
    pip install --upgrade pip && \
    pip install wheel setuptools==63.2.0 && \
    pip install -e '.[dev]' 
