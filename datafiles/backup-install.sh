#!/usr/bin/env bash
set -e

CONFIG_DIR="$SKALE_DIR"/config
CONTRACTS_DIR="$SKALE_DIR"/contracts_info
NODE_DATA_DIR=$SKALE_DIR/node_data

source "$DATAFILES_FOLDER"/helper.sh

tar -zxvf $BACKUP_PATH -C $HOME_DIR

echo "Creating .env symlink to $CONFIG_DIR/.env ..."
if [[ -f $CONFIG_DIR/.env ]]; then
    rm "$CONFIG_DIR/.env"
fi
ln -s $SKALE_DIR/.env $CONFIG_DIR/.env

cd $SKALE_DIR

iptables_configure
docker_lvmpy_install

cd $CONFIG_DIR
if [[ ! -z $CONTAINER_CONFIGS_DIR ]]; then
    echo "Building containers ..."
    SKALE_DIR=$SKALE_DIR docker-compose -f docker-compose.yml build
fi
up_compose