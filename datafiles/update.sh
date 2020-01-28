#!/usr/bin/env bash

CONFIG_DIR="$SKALE_DIR"/config
CONTRACTS_DIR="$SKALE_DIR"/contracts_info
NODE_DATA_DIR=$SKALE_DIR/node_data

source "$DATAFILES_FOLDER"/helper.sh

export $(grep -v '^#' $CONFIG_DIR/.env | xargs)

cd $SKALE_DIR
docker_lvmpy_update

dockerhub_login

remove_compose_containers
remove_dynamic_containers

cd $CONFIG_DIR
if [[ -z $CONTAINER_CONFIGS_DIR ]]; then
    git checkout $CONTAINER_CONFIGS_STREAM
    git pull
    docker-compose -f docker-compose.yml pull
else
    SKALE_DIR=$SKALE_DIR docker-compose -f docker-compose.yml build
fi
SKALE_DIR=$SKALE_DIR docker-compose -f docker-compose.yml up -d
