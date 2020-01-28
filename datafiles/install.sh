#!/usr/bin/env bash
set -e


#SKALE_DIR="$HOME"/.skale
CONFIG_DIR="$SKALE_DIR"/config
CONTRACTS_DIR="$SKALE_DIR"/contracts_info
NODE_DATA_DIR=$SKALE_DIR/node_data

source "$DATAFILES_FOLDER"/helper.sh

if [[ -z $CONTAINER_CONFIGS_DIR ]]; then
    rm -rf $CONFIG_DIR
    git clone https://$GITHUB_TOKEN\@github.com/skalenetwork/skale-node.git $CONFIG_DIR
    git checkout $CONTAINER_CONFIGS_STREAM
else
    rsync -r $CONTAINER_CONFIGS_DIR/* $CONFIG_DIR
    rsync -r $CONTAINER_CONFIGS_DIR/.git $CONFIG_DIR
fi

cd $SKALE_DIR

download_contracts
configure_filebeat
configure_flask

# Base policies (drop all incoming, allow all outcoming, drop all forwarding)
sudo iptables -P INPUT ALLOW
sudo iptables -P OUTPUT ACCEPT
sudo iptables -P FORWARD DROP
# Allow conntrack established connections
sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
# Allow local loopback services
sudo iptables -A INPUT -i lo -j ACCEPT
# Allow ssh
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
# Allow https
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
# Allow dns
sudo iptables -A INPUT -p tcp --dport 53 -j ACCEPT
sudo iptables -A INPUT -p udp --dport 53 -j ACCEPT  # mb useless
# Drop all the rest
sudo iptables -A INPUT -p tcp -j DROP
sudo iptables -A INPUT -p udp -j DROP
# Allow pings
sudo iptables -I INPUT -p icmp --icmp-type destination-unreachable -j ACCEPT
sudo iptables -I INPUT -p icmp --icmp-type source-quench -j ACCEPT
sudo iptables -I INPUT -p icmp --icmp-type time-exceeded -j ACCEPT
sudo iptables-save > /etc/iptables/rules.v4

if [[ -z $DRY_RUN ]]; then
    docker_lvmpy_install
    dockerhub_login # todo: remove after containers open-sourcing
    cd $CONFIG_DIR
    if [[ ! -z $CONTAINER_CONFIGS_DIR ]]; then
        SKALE_DIR=$SKALE_DIR docker-compose -f docker-compose.yml build
    fi
    SKALE_DIR=$SKALE_DIR docker-compose -f docker-compose.yml up -d
fi

