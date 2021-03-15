#!/usr/bin/env bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PROJECT_DIR=$(dirname $DIR)
export HIDE_STREAM_LOG=true
export HOME_DIR='tests/'

HOME_DIR='tests/' DOTENV_FILEPATH='tests/test-env' py.test tests/ --ignore=tests/operations/ $@
