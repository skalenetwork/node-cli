#!/usr/bin/env bash
set -e

CONFIG_DIR="$SKALE_DIR"/config
CONTRACTS_DIR="$SKALE_DIR"/contracts_info
NODE_DATA_DIR=$SKALE_DIR/node_data

source "$DATAFILES_FOLDER"/helper.sh

cd $SKALE_DIR

remove_compose_containers
remove_dynamic_containers

backup_old_contracts
download_contracts
docker_lvmpy_update

cd $CONFIG_DIR
if [[ -z $CONTAINER_CONFIGS_DIR ]]; then
    echo "Fetching new branches and tags..."
    git fetch
    echo "Checkouting to container configs branch $CONTAINER_CONFIGS_STREAM ..."
    git checkout $CONTAINER_CONFIGS_STREAM
    is_branch="$(git show-ref --verify refs/heads/$CONTAINER_CONFIGS_STREAM >/dev/null 2>&1; echo $?)"
    if [[ $is_branch -eq 0 ]] ; then
      echo "Pulling changes ..."
      git pull
    fi
    echo "Pulling new version of images ..."
    SKALE_DIR=$SKALE_DIR docker-compose -f docker-compose.yml pull
else
    echo "Syncing configs with CONTAINER_CONFIGS_DIR"
    # ls "$CONTAINER_CONFIGS_DIR/*"
    # rsync -r "$CONTAINER_CONFIGS_DIR/*" "$CONFIG_DIR"
    # rsync -r "$CONTAINER_CONFIGS_DIR/.git" "$CONFIG_DIR"
    echo "Building containers ..."
    SKALE_DIR=$SKALE_DIR docker-compose -f docker-compose.yml build
fi

download_filestorage_artifacts

up_compose
