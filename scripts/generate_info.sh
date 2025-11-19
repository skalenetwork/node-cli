#!/usr/bin/env bash
set -e

VERSION=$1
BRANCH=$2
TYPE_STR=$3

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
if [ -z "$TYPE_STR" ]; then
    (>&2 echo 'You should provide type: skale or fair')
    echo $USAGE_MSG
    exit 1
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PARENT_DIR="$(dirname "$DIR")"
DIST_INFO_FILEPATH=$PARENT_DIR/node_cli/cli/info.py

LATEST_COMMIT=$(git rev-parse HEAD)
CURRENT_DATETIME="$(date "+%Y-%m-%d %H:%M:%S")"
OS="$(uname -s)-$(uname -m)"

case "$TYPE_STR" in
    skale)
        TYPE_ENUM="NodeType.SKALE"
        ;;
    fair)
        TYPE_ENUM="NodeType.FAIR"
        ;;
    *)
        (>&2 echo "Error: Invalid type '$TYPE_STR'. Must be 'skale', or 'fair'")
        exit 1
        ;;
esac

rm -f "$DIST_INFO_FILEPATH"
touch "$DIST_INFO_FILEPATH"

echo "from node_cli.utils.node_type import NodeType" >> "$DIST_INFO_FILEPATH"
echo "" >> "$DIST_INFO_FILEPATH"

echo "BUILD_DATETIME = '$CURRENT_DATETIME'" >> "$DIST_INFO_FILEPATH"
echo "COMMIT = '$LATEST_COMMIT'" >> "$DIST_INFO_FILEPATH"
echo "BRANCH = '$BRANCH'" >> "$DIST_INFO_FILEPATH"
echo "OS = '$OS'" >> "$DIST_INFO_FILEPATH"
echo "VERSION = '$VERSION'" >> "$DIST_INFO_FILEPATH"
echo "TYPE = $TYPE_ENUM" >> "$DIST_INFO_FILEPATH"