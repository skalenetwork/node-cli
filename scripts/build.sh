#!/usr/bin/env bash
set -e

VERSION=$1
BRANCH=$2
TYPE=$3

cd "$(dirname "${BASH_SOURCE[0]}")/.."

bash scripts/generate_info.sh "$VERSION" "$BRANCH" "$TYPE"

EXECUTABLE_NAME=skale-$VERSION-$(uname -s)-$(uname -m)
if [ "$TYPE" = "fair" ]; then
    EXECUTABLE_NAME=$EXECUTABLE_NAME-fair
fi

pyinstaller main.spec

mv dist/main "dist/$EXECUTABLE_NAME"

echo "Built node-cli v$VERSION, branch: $BRANCH"
echo "Executable: $EXECUTABLE_NAME"
