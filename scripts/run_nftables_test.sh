#!/usr/bin/env bash
set -ea

# DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
# PROJECT_DIR=$(dirname $DIR)
# export DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

docker rm -f ncli-tester || true
docker build . -t ncli-tester
docker run \
    -e LVMPY_LOG_DIR="$PROJECT_DIR/tests/" \
    -e HIDE_STREAM_LOG=true \
    -e TEST_HOME_DIR="$PROJECT_DIR/tests/" \
    -e GLOBAL_SKALE_DIR="$PROJECT_DIR/tests/etc/skale" \
    -e DOTENV_FILEPATH='tests/test-env' \
    --cap-add=NET_ADMIN --cap-add=NET_RAW \
    --name ncli-tester ncli-tester py.test tests/core/migration_test.py tests/core/nftables_test.py $@

