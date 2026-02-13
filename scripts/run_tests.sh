#!/usr/bin/env bash

py.test --cov=$PROJECT_DIR/ --ignore=tests/core/nftables_test.py --ignore=tests/core/migration_test.py tests/ $@
