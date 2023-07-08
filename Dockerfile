FROM ubuntu:18.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get install -y  \
                       git \
                       python3.8 \
                       libpython3.8-dev \
                       python3.8-venv \
                       python3.8-distutils \
                       python3.8-dev \
                       build-essential \
                       zlib1g-dev \
                       libffi-dev \
                       libssl-dev \
                       swig \
                       iptables

RUN mkdir /app
WORKDIR /app

COPY . .

ENV PATH=/app/buildvenv/bin:$PATH
RUN python3.8 -m venv /app/buildvenv && \
    pip install --upgrade pip && \
    pip install wheel setuptools==63.2.0 && \
    pip install -e '.[dev]' 
