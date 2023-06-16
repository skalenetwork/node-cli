#!/usr/bin/env bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PROJECT_DIR=$(dirname $DIR)

LVMPY_LOG_DIR="$PROJECT_DIR/tests/" \
    HIDE_STREAM_LOG=true \
    TEST_HOME_DIR="$PROJECT_DIR/tests/" \
    GLOBAL_SKALE_DIR="$PROJECT_DIR/tests/etc/skale" \
    DOTENV_FILEPATH='tests/test-env' \
    py.test --cov=$PROJECT_DIR/ tests/ --ignore=tests/operations/ $@
