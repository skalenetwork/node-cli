#!/usr/bin/env bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PROJECT_DIR=$(dirname $DIR)

CONFIG_FILEPATH='tests/test-skale-cli.yaml' py.test tests/ $@
