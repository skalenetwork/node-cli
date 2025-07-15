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
    (>&2 echo 'You should provide type: normal, sync or fair')
    echo $USAGE_MSG
    exit 1
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PARENT_DIR="$(dirname "$DIR")"

OS=`uname -s`-`uname -m`

# Use the new generate_info.sh script
bash "${DIR}/generate_info.sh" "$VERSION" "$BRANCH" "$TYPE"

if [ "$TYPE" = "sync" ]; then
    EXECUTABLE_NAME=skale-$VERSION-$OS-sync
elif [ "$TYPE" = "fair" ]; then
    EXECUTABLE_NAME=skale-$VERSION-$OS-fair
else
    EXECUTABLE_NAME=skale-$VERSION-$OS
fi

pyinstaller main.spec

mv $PARENT_DIR/dist/main $PARENT_DIR/dist/$EXECUTABLE_NAME

echo "========================================================================================="
echo "Built node-cli v$VERSION, branch: $BRANCH"
echo "Executable: $EXECUTABLE_NAME"
