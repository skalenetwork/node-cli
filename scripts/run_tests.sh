#!/usr/bin/env bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PROJECT_DIR=$(dirname $DIR)

HOME_DIR='tests/' ENV=dev CONFIG_FILEPATH='tests/test-skalecli.yaml' DOTENV_FILEPATH='tests/test-env' py.test tests/ $@
