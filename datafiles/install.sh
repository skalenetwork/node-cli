#!/usr/bin/env bash
set -e

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

source helper.sh

check_env_variables
docker_lvmpy_install
create_node_dirs
copy_node_configs
download_contracts
configure_filebeat
configure_flask
generate_csr

if [ -z $DRY_RUN ]; then
    check_disk_mountpoint
    save_partition
    dockerhub_login # todo: remove after containers open-sourcing
    docker-compose -f $CONFIG_DIR/docker-compose.yml up -d
fi
