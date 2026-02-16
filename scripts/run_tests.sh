#!/usr/bin/env bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PROJECT_DIR=$(dirname $DIR)

. "$DIR/export_env.sh"

py.test --cov=$PROJECT_DIR/ --ignore=tests/core/nftables_test.py --ignore=tests/core/migration_test.py tests/ $@
