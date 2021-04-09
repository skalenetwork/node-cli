#!/usr/bin/env bash

echo "PROJECT_DIR=$GITHUB_WORKSPACE" >> $GITHUB_ENV

echo PROJECT_DIR: $GITHUB_WORKSPACE

export BRANCH=${GITHUB_REF##*/}
echo "Branch $BRANCH"

export VERSION=$(python setup.py --version)
export VERSION=$(bash ./helper-scripts/calculate_version.sh)

echo "VERSION=$VERSION" >> $GITHUB_ENV
echo "Version $VERSION"

export OS=`uname -s`-`uname -m`
export EXECUTABLE_NAME=skale-$VERSION-$OS

echo "BRANCH=$BRANCH" >> $GITHUB_ENV
echo "EXECUTABLE_NAME=$EXECUTABLE_NAME" >> $GITHUB_ENV
