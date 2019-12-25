#!/usr/bin/env bash

# curl -fsSL https://get.docker.com -o get-docker.sh
# sh get-docker.sh

sudo curl -L "https://github.com/docker/compose/releases/download/1.23.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose


while ! (ps -ef | grep "[d]ocker" | awk {'print $2'});
do
  echo "Waiting for docker daemon file..."
  sleep 5
done
