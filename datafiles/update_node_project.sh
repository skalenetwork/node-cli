#!/bin/bash

SKALE_DIR="$HOME"/.skale
SKALE_NODE_DIR_NAME=.skale-node
SKALE_NODE_DIR="$SKALE_DIR"/"$SKALE_NODE_DIR_NAME"

cd $SKALE_NODE_DIR
sudo git pull
