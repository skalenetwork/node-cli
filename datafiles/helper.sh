#!/usr/bin/env bash

export FLASK_SECRET_KEY_FILE=$NODE_DATA_DIR/flask_db_key.txt
export DISK_MOUNTPOINT_FILE=$NODE_DATA_DIR/disk_mountpoint.txt
export SGX_CERTIFICATES_DIR_NAME=sgx_certs

export FILESTORAGE_INFO_FILE=$SKALE_DIR/config/filestorage_info.json
export FILESTORAGE_ARTIFACTS_FILE=$NODE_DATA_DIR/filestorage_artifacts.json

export CONTRACTS_DIR="$SKALE_DIR"/contracts_info
export BACKUP_CONTRACTS_DIR="$SKALE_DIR"/.old_contracts_info

export BASE_SERVICES="transaction-manager skale-admin skale-api mysql sla bounty watchdog filebeat"
export NOTIFICATION_SERVICES="celery redis"

remove_dynamic_containers () {
    echo 'Removing schains containers ...'
    SCHAIN_CONTAINERS="$(docker ps -a --format '{{.Names}}' | grep '^skale_schain_' | awk '{print $1}' | xargs)"
    for CONTAINER in $SCHAIN_CONTAINERS; do
        echo 'Stopping' $CONTAINER
        docker stop $CONTAINER -t 40
        echo 'Removing' $CONTAINER
        docker rm $CONTAINER
    done

    echo 'Removing ima containers...'
    IMA_CONTAINERS="$(docker ps -a --format '{{.Names}}' | grep '^skale_ima_' | awk '{print $1}' | xargs)"
    for CONTAINER in $IMA_CONTAINERS; do
        echo 'Stopping' $CONTAINER
        docker stop $CONTAINER -t 40
        echo 'Removing' $CONTAINER
        docker rm $CONTAINER
    done
}

remove_compose_containers () {
    echo 'Removing node containers ...'
    COMPOSE_PATH=$SKALE_DIR/config/docker-compose.yml
    echo 'Removing api, sla, bounty, admin containers ...'
    DB_PORT=0 docker-compose -f  $COMPOSE_PATH rm  -s -f skale-api sla bounty skale-admin
    echo 'Api, sla, bounty, admin containers were removed. Sleeping ...'
    sleep 7
    echo 'Removing transaction-manager, mysql and rest ...'
    DB_PORT=0 docker-compose -f $COMPOSE_PATH  rm  -s -f
    echo 'Done'
}

download_contracts () {
    echo "Downloading contracts ABI ..."
    curl -L $MANAGER_CONTRACTS_ABI_URL > $CONTRACTS_DIR/manager.json
    curl -L $IMA_CONTRACTS_ABI_URL > $CONTRACTS_DIR/ima.json
}

download_filestorage_artifacts () {
    echo "Downloading filestorage artifacts ..."
    FS_ARTIFACTS_URL=$(cat $FILESTORAGE_INFO_FILE | sed -n 's/^[[:space:]]*"artifacts_url"[[:space:]]*:[[:space:]]*//p')
    FS_ARTIFACTS_URL=$(echo "$FS_ARTIFACTS_URL" | sed -r 's/["]+//g')
    curl -L $FS_ARTIFACTS_URL > $FILESTORAGE_ARTIFACTS_FILE
}

backup_old_contracts () {
    echo "Copying old contracts ABI ..."
    cp -R $CONTRACTS_DIR $BACKUP_CONTRACTS_DIR
}


update_docker_lvmpy_sources () {
    echo 'Updating docker-lvmpy sources ...'
    cd docker-lvmpy
    echo "Fetching changes ..."
    git fetch
    echo "Checkouting to $DOCKER_LVMPY_STREAM ..."
    git checkout $DOCKER_LVMPY_STREAM
    is_branch="$(git show-ref --verify refs/heads/$DOCKER_LVMPY_STREAM > /dev/null 2>&1; echo $?)"
    if [[ $is_branch -eq 0 ]] ; then
      echo "Pulling recent changes from $DOCKER_LVMPY_STREAM ..."
      git pull
    fi
}

docker_lvmpy_install () {
    echo 'Installing docker-lvmpy ...'
    if [[ ! -d docker-lvmpy ]]; then
        git clone "https://github.com/skalenetwork/docker-lvmpy.git"
    fi
    update_docker_lvmpy_sources
    echo "Running install.sh script ..."
    sudo -H PHYSICAL_VOLUME=$DISK_MOUNTPOINT VOLUME_GROUP=schains PATH=$PATH scripts/install.sh
    cd -
}

docker_lvmpy_update () {
    update_docker_lvmpy_sources
    echo "Running update.sh script ..."
    sudo -H PHYSICAL_VOLUME=$DISK_MOUNTPOINT VOLUME_GROUP=schains PATH=$PATH scripts/update.sh
    cd -
}

iptables_configure() {
    echo "Configuring iptables ..."
    mkdir -p /etc/iptables/
    # Base policies (drop all incoming, allow all outcoming, drop all forwarding)
    sudo iptables -P INPUT ACCEPT
    sudo iptables -P OUTPUT ACCEPT
    sudo iptables -P FORWARD DROP
    # Allow conntrack established connections
    sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
    # Allow local loopback services
    sudo iptables -A INPUT -i lo -j ACCEPT
    # Allow ssh
    sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
    # Allow http
    sudo iptables -A INPUT -p tcp --dport 8080 -j ACCEPT
    # Allow https
    sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
    # Allow dns
    sudo iptables -A INPUT -p tcp --dport 53 -j ACCEPT
    sudo iptables -A INPUT -p udp --dport 53 -j ACCEPT
    # Allow watchdog
    sudo iptables -A INPUT -p tcp --dport 3009 -j ACCEPT
    # Allow monitor node exporter
    sudo iptables -A INPUT -p tcp --dport 9100 -j ACCEPT
    # Drop all the rest
    sudo iptables -A INPUT -p tcp -j DROP
    sudo iptables -A INPUT -p udp -j DROP
    # Allow pings
    sudo iptables -I INPUT -p icmp --icmp-type destination-unreachable -j ACCEPT
    sudo iptables -I INPUT -p icmp --icmp-type source-quench -j ACCEPT
    sudo iptables -I INPUT -p icmp --icmp-type time-exceeded -j ACCEPT
    sudo bash -c 'iptables-save > /etc/iptables/rules.v4'
}

configure_flask () {
    echo "Configuring flask secret key ..."
    if [ -e $FLASK_SECRET_KEY_FILE ]; then
      echo "File $FLASK_SECRET_KEY_FILE already exists!"
    else
      FLASK_SECRET_KEY=$(openssl rand -base64 32)
      echo $FLASK_SECRET_KEY >> $FLASK_SECRET_KEY_FILE
    fi
    export FLASK_SECRET_KEY=$FLASK_SECRET_KEY
}

configure_filebeat () {
    echo "Configuring filebeat ..."
    sudo cp $CONFIG_DIR/filebeat.yml $NODE_DATA_DIR/
    sudo chown root $NODE_DATA_DIR/filebeat.yml
    sudo chmod go-w $NODE_DATA_DIR/filebeat.yml
}

up_compose() {
    if [[ "$MONITORING_CONTAINERS" == "True"  ]]; then
        echo "Running SKALE Node with monitoring containers..."
        SKALE_DIR="$SKALE_DIR" docker-compose -f docker-compose.yml up -d
    else
        echo "Running SKALE Node with base set of containers..."
        SKALE_DIR="$SKALE_DIR" docker-compose -f docker-compose.yml up -d $BASE_SERVICES
    fi
    if [[ ! -z "$TG_API_KEY" && ! -z "$TG_CHAT_ID" ]]; then
        SKALE_DIR="$SKALE_DIR" docker-compose -f docker-compose.yml up -d $NOTIFICATION_SERVICES
        echo "Running containers for telegram notifications..."
    fi
}
