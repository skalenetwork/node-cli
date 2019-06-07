#!/usr/bin/env bash

sudo mkdir -p /skale
#sudo chown -R $USER: /skale
cd /skale

sudo git clone -b $GIT_BRANCH https://$GITHUB_TOKEN\@github.com/skalenetwork/skale-node.git
cp -f /tmp/data.json ./skale-node/config/data.json

cd /skale/skale-node/installation
DOCKER_USERNAME=$DOCKER_USERNAME DOCKER_PASSWORD=$DOCKER_PASSWORD RUN_MODE=admin RPC_IP=$RPC_IP RPC_PORT=$RPC_PORT \
    DB_USER=$DB_USER DB_PASSWORD=$DB_PASSWORD CUSTOM_CONTRACTS=true sudo -E bash install.sh
