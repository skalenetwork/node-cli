#!/usr/bin/env bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PROJECT_DIR=$(dirname $DIR)

HIDE_STREAM_LOG=true HOME_DIR='tests/' GLOBAL_SKALE_DIR='tests/etc/skale' DOTENV_FILEPATH='tests/test-env' py.test --cov=$PROJECT_DIR/ tests/ --ignore=tests/operations/ $@
