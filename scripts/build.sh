#!/usr/bin/env bash

set -e

VERSION=$1
BRANCH=$2
TYPE=$3

USAGE_MSG='Usage: build.sh [VERSION] [BRANCH] [TYPE]'

if [ -z "$1" ]
then
    (>&2 echo 'You should provide version')
    echo $USAGE_MSG
    exit 1
fi

if [ -z "$2" ]
then
    (>&2 echo 'You should provide git branch')
    echo $USAGE_MSG
    exit 1
fi

if [ -z "$3" ]
then
    (>&2 echo 'You should provide type: normal or sync')
    echo $USAGE_MSG
    exit 1
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PARENT_DIR="$(dirname "$DIR")"

OS=`uname -s`-`uname -m`
#CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
LATEST_COMMIT=$(git rev-parse HEAD)
CURRENT_DATETIME="`date "+%Y-%m-%d %H:%M:%S"`";
DIST_INFO_FILEPATH=$PARENT_DIR/node_cli/cli/info.py

touch $DIST_INFO_FILEPATH

echo "BUILD_DATETIME = '$CURRENT_DATETIME'" > $DIST_INFO_FILEPATH
echo "COMMIT = '$LATEST_COMMIT'" >> $DIST_INFO_FILEPATH
echo "BRANCH = '$BRANCH'" >> $DIST_INFO_FILEPATH
echo "OS = '$OS'" >> $DIST_INFO_FILEPATH
echo "VERSION = '$VERSION'" >> $DIST_INFO_FILEPATH
echo "TYPE = '$TYPE'" >> $DIST_INFO_FILEPATH

if [ "$TYPE" = "sync" ]; then
    EXECUTABLE_NAME=skale-$VERSION-$OS-sync
else
    EXECUTABLE_NAME=skale-$VERSION-$OS
fi

pyinstaller --onefile main.spec

mv $PARENT_DIR/dist/main $PARENT_DIR/dist/$EXECUTABLE_NAME

echo "========================================================================================="
echo "Built node-cli v$VERSION, branch: $BRANCH"
echo "Executable: $EXECUTABLE_NAME"
