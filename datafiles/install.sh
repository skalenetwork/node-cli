#!/usr/bin/env bash
set -e


SKALE_DIR="$HOME"/.skale
CONFIG_DIR="$SKALE_DIR"/config
CONTRACTS_DIR="$SKALE_DIR"/contracts_info
NODE_DATA_DIR=$SKALE_DIR/node_data

source "$DATAFILES_FOLDER"/helper.sh
ls -latr $CONFIG_DIR

if [[ -z $SKALE_NODE_SOURCE ]]; then
    rm -rf $CONFIG_DIR
    sudo git clone -b $GIT_BRANCH https://$GITHUB_TOKEN\@github.com/skalenetwork/skale-node.git $CONFIG_DIR
else
    rsync -r $SKALE_NODE_SOURCE/* $CONFIG_DIR
fi

mv $SKALE_DIR/.env $CONFIG_DIR/


ls -latr $CONFIG_DIR

cd $SKALE_DIR


download_contracts
configure_filebeat
configure_flask

if [[ -z $DRY_RUN ]]; then
    docker_lvmpy_install
    dockerhub_login # todo: remove after containers open-sourcing
    cd $CONFIG_DIR
    if [[ ! -z $SKALE_NODE_SOURCE ]]; then
        SKALE_DIR=$SKALE_DIR docker-compose -f $CONFIG_DIR/docker-compose.yml build
    fi
    SKALE_DIR=$SKALE_DIR docker-compose -f docker-compose.yml up -d
fi
