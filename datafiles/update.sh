#!/usr/bin/env bash
set -e

CONFIG_DIR="$SKALE_DIR"/config
CONTRACTS_DIR="$SKALE_DIR"/contracts_info
NODE_DATA_DIR=$SKALE_DIR/node_data

source "$DATAFILES_FOLDER"/helper.sh

cd $SKALE_DIR

export $(grep -v '^#' .env | xargs)

remove_compose_containers
remove_dynamic_containers

backup_old_contracts
download_contracts
docker_lvmpy_update

cd $CONFIG_DIR
if [[ -z $CONTAINER_CONFIGS_DIR ]]; then
    echo "Checkouting to container configs branch $CONTAINER_CONFIGS_STREAM ..."
    git checkout $CONTAINER_CONFIGS_STREAM
    echo "Pulling changes ..."
    git pull
    echo "Pulling new version of images ..."
    SKALE_DIR=$SKALE_DIR docker-compose -f docker-compose.yml pull
else
    echo "Building containers ..."
    SKALE_DIR=$SKALE_DIR docker-compose -f docker-compose.yml build
fi
up_compose
