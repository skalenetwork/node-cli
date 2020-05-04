#!/usr/bin/env bash

export FLASK_SECRET_KEY_FILE=$NODE_DATA_DIR/flask_db_key.txt
export DISK_MOUNTPOINT_FILE=$NODE_DATA_DIR/disk_mountpoint.txt
export SGX_CERTIFICATES_DIR_NAME=sgx_certs

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
    DB_PORT=0 docker-compose -f $SKALE_DIR/config/docker-compose.yml rm  -s -f
}

download_contracts () {
    echo "Downloading contracts abi ..."
    curl -L $MANAGER_CONTRACTS_ABI_URL > $CONTRACTS_DIR/manager.json
    curl -L $IMA_CONTRACTS_ABI_URL > $CONTRACTS_DIR/ima.json
}

docker_lvmpy_install () {
    if [[ ! -d docker-lvmpy ]]; then
        git clone "https://github.com/skalenetwork/docker-lvmpy.git"
    fi
    cd docker-lvmpy
    echo "Checkouting to $DOCKER_LVMPY_STREAM ..."
    git checkout $DOCKER_LVMPY_STREAM
    echo "Running install.sh script ..."
    PHYSICAL_VOLUME=$DISK_MOUNTPOINT VOLUME_GROUP=schains PATH=$PATH scripts/install.sh
    cd -
}

docker_lvmpy_update () {
    echo 'Updating docker-lvmpy ...'
    cd docker-lvmpy
    echo "Checkouting to $DOCKER_LVMPY_STREAM ..."
    git checkout $DOCKER_LVMPY_STREAM
    echo "Pulling changes ..."
    git pull
    echo "Running update.sh script ..."
    PHYSICAL_VOLUME=$DISK_MOUNTPOINT VOLUME_GROUP=schains PATH=$PATH scripts/update.sh
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
    # Drop all the rest
    sudo iptables -A INPUT -p tcp -j DROP
    sudo iptables -A INPUT -p udp -j DROP
    # Allow pings
    sudo iptables -I INPUT -p icmp --icmp-type destination-unreachable -j ACCEPT
    sudo iptables -I INPUT -p icmp --icmp-type source-quench -j ACCEPT
    sudo iptables -I INPUT -p icmp --icmp-type time-exceeded -j ACCEPT
    sudo iptables-save > /etc/iptables/rules.v4
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
    cp $CONFIG_DIR/filebeat.yml $NODE_DATA_DIR/
}
