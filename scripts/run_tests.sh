#!/usr/bin/env bash

. "$(dirname "${BASH_SOURCE[0]}")/export_env.sh"

pytest --ignore=tests/core/nftables_test.py --ignore=tests/core/monitoring_firewall_test.py tests/ "$@"
