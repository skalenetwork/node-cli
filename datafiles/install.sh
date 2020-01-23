#!/usr/bin/env bash

SKALE_DIR="$HOME"/.skale
SKALE_NODE_DIR_NAME=.skale-node
SKALE_NODE_DIR="$SKALE_DIR"/"$SKALE_NODE_DIR_NAME"

mkdir -p $SKALE_DIR
cd $SKALE_DIR

rm -rf $SKALE_NODE_DIR

if [[ -z $SKALE_NODE_SOURCE ]]; then
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

sudo -E bash install.sh
