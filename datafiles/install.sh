#!/usr/bin/env bash

SKALE_DIR="$HOME"/.skale
SKALE_NODE_DIR_NAME=.skale-node
SKALE_NODE_DIR="$SKALE_DIR"/"$SKALE_NODE_DIR_NAME"

mkdir -p $SKALE_DIR
cd $SKALE_DIR

rm -rf $SKALE_NODE_DIR

if [[ -z $"{SKALE_NODE_SOURCE}" ]]; then
    sudo git clone -b $GIT_BRANCH https://$GITHUB_TOKEN\@github.com/skalenetwork/skale-node.git .skale-node
else
    rsync -r $SKALE_NODE_SOURCE/* .skale-node
fi

umount $DISK_MOUNTPOINT

cd "$SKALE_NODE_DIR"/scripts

export DOCKER_USERNAME=$DOCKER_USERNAME
export DOCKER_PASSWORD=$DOCKER_PASSWORD

export DISK_MOUNTPOINT=$DISK_MOUNTPOINT
export ENDPOINT=$ENDPOINT
export IMA_ENDPOINT=$IMA_ENDPOINT

export MANAGER_CONTRACTS_INFO_URL=$MANAGER_CONTRACTS_INFO_URL
export IMA_CONTRACTS_INFO_URL=$IMA_CONTRACTS_INFO_URL

export DB_USER=$DB_USER
export DB_PORT=$DB_PORT
export DB_PASSWORD=$DB_PASSWORD
export DB_ROOT_PASSWORD=$DB_ROOT_PASSWORD

sudo -E bash install.sh
