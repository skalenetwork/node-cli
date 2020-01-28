#!/usr/bin/env bash

export FLASK_SECRET_KEY_FILE=$NODE_DATA_DIR/flask_db_key.txt
export DISK_MOUNTPOINT_FILE=$NODE_DATA_DIR/disk_mountpoint.txt
export SGX_CERTIFICATES_DIR_NAME=sgx_certs

remove_dynamic_containers () {
    docker ps -a --format '{{.Names}}' | grep "^skale_schain_" | awk '{print $1}' | xargs -I {} docker rm -f {}
    docker ps -a --format '{{.Names}}' | grep "^skale_ima_" | awk '{print $1}' | xargs -I {} docker rm -f {}
}

remove_compose_containers () {
   DB_PORT=0 docker-compose -f $SKALE_DIR/config/docker-compose.yml rm  -s -f
}

download_contracts () {
    curl -L $MANAGER_CONTRACTS_ABI_URL > $CONTRACTS_DIR/manager.json
    curl -L $IMA_CONTRACTS_ABI_URL > $CONTRACTS_DIR/ima.json
}

dockerhub_login () {
    echo "$DOCKER_PASSWORD" | docker login --username $DOCKER_USERNAME --password-stdin # todo: remove after containers open-sourcing
}


docker_lvmpy_install () {
    if [[ ! -d docker-lvmpy ]]; then
        git clone "https://github.com/skalenetwork/docker-lvmpy.git"
    fi
    cd docker-lvmpy
    git checkout $DOCKER_LVMPY_STREAM
    PHYSICAL_VOLUME=$DISK_MOUNTPOINT VOLUME_GROUP=schains PATH=$PATH scripts/install.sh
    cd -
}

docker_lvmpy_update () {
    cd docker-lvmpy
    git checkout $DOCKER_LVMPY_STREAM
    git pull
    PHYSICAL_VOLUME=$DISK_MOUNTPOINT VOLUME_GROUP=schains PATH=$PATH scripts/update.sh
    cd -
}

configure_flask () {
    if [ -e $FLASK_SECRET_KEY_FILE ]; then
      echo "File $FLASK_SECRET_KEY_FILE already exists!"
    else
      FLASK_SECRET_KEY=$(openssl rand -base64 32)
      echo $FLASK_SECRET_KEY >> $FLASK_SECRET_KEY_FILE
    fi
    export FLASK_SECRET_KEY=$FLASK_SECRET_KEY
}

configure_filebeat () {
    cp $CONFIG_DIR/filebeat.yml $NODE_DATA_DIR/
}
