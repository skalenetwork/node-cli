#!/usr/bin/env bash
set -e

docker build . -t ncli-tester
docker run --rm --cap-add=NET_ADMIN --cap-add=NET_RAW ncli-tester bash -c \
    '. scripts/export_env.sh && pytest tests/core/nftables_test.py tests/core/monitoring_firewall_test.py "$@"' _ "$@"
