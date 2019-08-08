#!/usr/bin/env bash

sudo mkdir -p /skale
#sudo chown -R $USER: /skale
cd /skale

sudo git clone -b $GIT_BRANCH https://$GITHUB_TOKEN\@github.com/skalenetwork/skale-node.git
#cp -f /tmp/data.json ./skale-node/config/data.json

umount $DISK_MOUNTPOINT

cd /skale/skale-node/installation
DOCKER_USERNAME=$DOCKER_USERNAME DOCKER_PASSWORD=$DOCKER_PASSWORD RUN_MODE=prod RPC_IP=$RPC_IP \
    RPC_PORT=$RPC_PORT DB_USER=$DB_USER DB_PASSWORD=$DB_PASSWORD DB_ROOT_PASSWORD=$DB_ROOT_PASSWORD \
    CUSTOM_CONTRACTS=true DISK_MOUNTPOINT=$DISK_MOUNTPOINT DB_PORT=$DB_PORT MTA_ENDPOINT=$MTA_ENDPOINT sudo -E bash install.sh
