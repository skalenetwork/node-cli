#!/usr/bin/env bash

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
CURRENT_VERSION="$(python $DIR/cli/__init__.py)"
VERSION_FILE=$DIR/cli/__init__.py
OS=`uname -s`-`uname -m`
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
LATEST_COMMIT=$(git rev-parse HEAD)
CURRENT_DATETIME="`date "+%Y-%m-%d %H:%M:%S"`";
DIST_INFO_FILEPATH=$DIR/cli/info.py

NOT_VALID_BUMP_LEVEL_TEXT="Please provide bump level: major/minor/patch/keep"

if [ -z "$1" ]
then
    (>&2 echo $NOT_VALID_BUMP_LEVEL_TEXT)
    exit 1
fi

if [ "$1" != "keep" ]
then
    RES=`bumpversion --allow-dirty --current-version $CURRENT_VERSION $1 $VERSION_FILE`
fi

VERSION="$(python setup.py --version)"

if [ "$CURRENT_BRANCH" == "stable" ]
then
    FULL_VERSION=$VERSION
else
    FULL_VERSION=$VERSION.$CURRENT_BRANCH
fi


echo "BUILD_DATETIME = '$CURRENT_DATETIME'" > $DIST_INFO_FILEPATH
echo "COMMIT = '$LATEST_COMMIT'" >> $DIST_INFO_FILEPATH
echo "BRANCH = '$CURRENT_BRANCH'" >> $DIST_INFO_FILEPATH
echo "OS = '$OS'" >> $DIST_INFO_FILEPATH
echo "VERSION = '$FULL_VERSION'" >> $DIST_INFO_FILEPATH


EXECUTABLE_NAME=skale-$FULL_VERSION-$OS

pyinstaller --onefile main.spec --hidden-import=eth_hash.backends.pysha3

mv $DIR/dist/main $DIR/dist/$EXECUTABLE_NAME

echo "========================================================================================="
echo "Bumped $CURRENT_VERSION → $VERSION ($1 release), branch: $CURRENT_BRANCH"
echo "Executable: $EXECUTABLE_NAME"
