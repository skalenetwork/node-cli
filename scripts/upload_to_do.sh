#!/usr/bin/env bash

python $TRAVIS_BUILD_DIR/scripts/upload_to_do.py $TRAVIS_BUILD_DIR/dist/$EXECUTABLE_NAME skale-cli $TRAVIS_BRANCH/$EXECUTABLE_NAME