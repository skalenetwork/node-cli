#!/usr/bin/env bash

echo "::set-env name=PROJECT_DIR::$GITHUB_WORKSPACE"
echo PROJECT_DIR: $GITHUB_WORKSPACE

export BRANCH=${GITHUB_REF##*/}
echo "Branch $BRANCH"

export VERSION=$(python setup.py --version)
export VERSION=$(bash ./helper-scripts/calculate_version.sh)

echo "::set-env name=VERSION::$VERSION"
echo "Version $VERSION"

export OS=`uname -s`-`uname -m`
export EXECUTABLE_NAME=skale-$VERSION-$OS

echo "::set-env name=BRANCH::$BRANCH"
echo "::set-env name=EXECUTABLE_NAME::$EXECUTABLE_NAME"
