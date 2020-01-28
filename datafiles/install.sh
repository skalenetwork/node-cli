#!/usr/bin/env bash
set -e


#SKALE_DIR="$HOME"/.skale
CONFIG_DIR="$SKALE_DIR"/config
CONTRACTS_DIR="$SKALE_DIR"/contracts_info
NODE_DATA_DIR=$SKALE_DIR/node_data

source "$DATAFILES_FOLDER"/helper.sh

if [[ -z $CONTAINER_CONFIGS_DIR ]]; then
    rm -rf $CONFIG_DIR
    git clone https://$GITHUB_TOKEN\@github.com/skalenetwork/skale-node.git $CONFIG_DIR
    git checkout $CONTAINER_CONFIGS_STREAM
else
    rsync -r $CONTAINER_CONFIGS_DIR/* $CONFIG_DIR
    rsync -r $CONTAINER_CONFIGS_DIR/.git $CONFIG_DIR
fi

cd $SKALE_DIR

download_contracts
configure_filebeat
configure_flask

if [[ -z $DRY_RUN ]]; then
    docker_lvmpy_install
    dockerhub_login # todo: remove after containers open-sourcing
    cd $CONFIG_DIR
    if [[ ! -z $CONTAINER_CONFIGS_DIR ]]; then
        SKALE_DIR=$SKALE_DIR docker-compose -f docker-compose.yml build
    fi
    SKALE_DIR=$SKALE_DIR docker-compose -f docker-compose.yml up -d
fi
