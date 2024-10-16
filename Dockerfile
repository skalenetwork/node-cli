FROM python:3.11-buster

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y software-properties-common
RUN apt-get install -y  \
                       git \
                       build-essential \
                       zlib1g-dev \
                       libssl-dev \
                       libffi-dev \
                       swig \
                       iptables

RUN mkdir /app
WORKDIR /app

COPY . .

ENV PATH=/app/buildvenv/bin:$PATH
RUN python3.11 -m venv /app/buildvenv && \
    pip install --upgrade pip && \
    pip install wheel setuptools==63.2.0 && \
    pip install -e '.[dev]' 
