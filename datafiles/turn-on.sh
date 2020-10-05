#!/usr/bin/env bash
set -e

CONFIG_DIR="$SKALE_DIR"/config
CONTRACTS_DIR="$SKALE_DIR"/contracts_info
NODE_DATA_DIR=$SKALE_DIR/node_data

source "$DATAFILES_FOLDER"/helper.sh

cd $SKALE_DIR

export $(grep -v '^#' .env | xargs)

cd $CONFIG_DIR
up_compose
