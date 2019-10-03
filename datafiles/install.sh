#!/usr/bin/env bash

REPO_NAME=skale-node

sudo mkdir -p /skale
#sudo chown -R $USER: /skale
cd /skale

sudo git clone -b $GIT_BRANCH https://$GITHUB_TOKEN\@github.com/skalenetwork/$REPO_NAME.git
#cp -f /tmp/data.json ./skale-node/config/data.json

umount $DISK_MOUNTPOINT

cd /skale/$REPO_NAME/scripts

export DOCKER_USERNAME=$DOCKER_USERNAME
export DOCKER_PASSWORD=$DOCKER_PASSWORD

export DISK_MOUNTPOINT=$DISK_MOUNTPOINT
export ENDPOINT=$ENDPOINT
export IMA_ENDPOINT=$IMA_ENDPOINT

export MANAGER_CONTRACTS_INFO_URL=$MANAGER_CONTRACTS_INFO_URL
export IMA_CONTRACTS_INFO_URL=$IMA_CONTRACTS_INFO_URL
export DKG_CONTRACTS_INFO_URL=$DKG_CONTRACTS_INFO_URL

export DB_USER=$DB_USER
export DB_PORT=$DB_PORT
export DB_PASSWORD=$DB_PASSWORD
export DB_ROOT_PASSWORD=$DB_ROOT_PASSWORD

sudo -E bash install.sh