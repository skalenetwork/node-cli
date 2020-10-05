#!/usr/bin/env bash
set -e

source "$DATAFILES_FOLDER"/helper.sh

export $(grep -v '^#' .env | xargs)

remove_compose_containers
remove_dynamic_containers
