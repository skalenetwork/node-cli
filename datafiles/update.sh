#!/usr/bin/env bash

SKALE_DIR="$HOME"/.skale
SKALE_NODE_DIR_NAME=.skale-node
SKALE_NODE_DIR="$SKALE_DIR"/"$SKALE_NODE_DIR_NAME"

cd $SKALE_NODE_DIR
sudo git pull

source helper.sh

check_env_variables
dockerhub_login
# docker_lvmpy_install

remove_compose_containers
remove_dynamic_containers

rm -rf /tmp/.skale
cp -r $CONFIG_DIR /tmp/.skale
rm -rf $CONFIG_DIR

mkdir -p $CONFIG_DIR
copy_node_configs

download_contracts

docker-compose -f $CONFIG_DIR/docker-compose.yml pull
docker-compose -f $CONFIG_DIR/docker-compose.yml up -d
