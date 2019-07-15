#!/usr/bin/env bash

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
CURRENT_VERSION="$(python setup.py --version)"
VERSION_FILE=$DIR/cli/__init__.py
OS=`uname -s`-`uname -m`


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
EXECUTABLE_NAME=skale-$VERSION-$OS

pyinstaller --onefile main.spec

mv $DIR/dist/main $DIR/dist/$EXECUTABLE_NAME

echo "Bumped $CURRENT_VERSION → $VERSION ($1 release)"
echo "Executable: $EXECUTABLE_NAME"
