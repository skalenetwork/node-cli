#!/usr/bin/env bash
set -e

VERSION=$1
BRANCH=$2
TYPE=$3

USAGE_MSG='Usage: generate_info.sh [VERSION] [BRANCH] [TYPE]'

if [ -z "$VERSION" ]; then
    (>&2 echo 'You should provide version')
    echo $USAGE_MSG
    exit 1
fi
if [ -z "$BRANCH" ]; then
    (>&2 echo 'You should provide git branch')
    echo $USAGE_MSG
    exit 1
fi
if [ -z "$TYPE" ]; then
    (>&2 echo 'You should provide type: normal or sync')
    echo $USAGE_MSG
    exit 1
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PARENT_DIR="$(dirname "$DIR")"
DIST_INFO_FILEPATH=$PARENT_DIR/node_cli/cli/info.py

LATEST_COMMIT=$(git rev-parse HEAD)
CURRENT_DATETIME="$(date "+%Y-%m-%d %H:%M:%S")"
OS="$(uname -s)-$(uname -m)"

rm -f "$DIST_INFO_FILEPATH"
touch "$DIST_INFO_FILEPATH"

echo "BUILD_DATETIME = '$CURRENT_DATETIME'" >> "$DIST_INFO_FILEPATH"
echo "COMMIT = '$LATEST_COMMIT'" >> "$DIST_INFO_FILEPATH"
echo "BRANCH = '$BRANCH'" >> "$DIST_INFO_FILEPATH"
echo "OS = '$OS'" >> "$DIST_INFO_FILEPATH"
echo "VERSION = '$VERSION'" >> "$DIST_INFO_FILEPATH"
echo "TYPE = '$TYPE'" >> "$DIST_INFO_FILEPATH"
