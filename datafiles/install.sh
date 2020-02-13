#!/usr/bin/env bash
set -e

CONFIG_DIR="$SKALE_DIR"/config
CONTRACTS_DIR="$SKALE_DIR"/contracts_info
NODE_DATA_DIR=$SKALE_DIR/node_data

source "$DATAFILES_FOLDER"/helper.sh

if [[ -z $CONTAINER_CONFIGS_DIR ]]; then
    cd $CONFIG_DIR
    echo "Cloning container configs ..."
    git clone https://github.com/skalenetwork/skale-node.git .
    echo "Checkouting to container configs branch $CONTAINER_CONFIGS_STREAM ..."
    git checkout $CONTAINER_CONFIGS_STREAM
else
    echo "Syncing container configs ..."
    rsync -r $CONTAINER_CONFIGS_DIR/* $CONFIG_DIR
    rsync -r $CONTAINER_CONFIGS_DIR/.git $CONFIG_DIR
fi

echo "Creating .env symlink to $CONFIG_DIR/.env ..."
ln -s $SKALE_DIR/.env $CONFIG_DIR/.env

cd $SKALE_DIR

download_contracts
configure_filebeat
configure_flask
iptables_configure

if [[ -z $DRY_RUN ]]; then
    docker_lvmpy_install
    dockerhub_login # todo: remove after containers open-sourcing
    cd $CONFIG_DIR
    if [[ ! -z $CONTAINER_CONFIGS_DIR ]]; then
        echo "Building containers ..."
        SKALE_DIR=$SKALE_DIR docker-compose -f docker-compose.yml build
    fi
    echo "Creating containers ..."
    SKALE_DIR=$SKALE_DIR docker-compose -f docker-compose.yml up -d
fi

