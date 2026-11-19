#!/usr/bin/env bash
set -e

VERSION=$1
BRANCH=$2
TYPE=$3

if [ -z "$VERSION" ] || [ -z "$BRANCH" ] || [[ ! "$TYPE" =~ ^(skale|fair)$ ]]; then
    echo 'Usage: generate_info.sh VERSION BRANCH skale|fair' >&2
    exit 1
fi

COMMIT=$(git rev-parse HEAD)

cat > "$(dirname "${BASH_SOURCE[0]}")/../node_cli/cli/info.py" <<EOF
from node_cli.utils.node_type import NodeType

BUILD_DATETIME = '$(date '+%Y-%m-%d %H:%M:%S')'
COMMIT = '$COMMIT'
BRANCH = '$BRANCH'
OS = '$(uname -s)-$(uname -m)'
VERSION = '$VERSION'
TYPE = NodeType('$TYPE')
EOF
