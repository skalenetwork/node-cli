#!/usr/bin/env bash
set -e

source "$DATAFILES_FOLDER"/helper.sh

remove_compose_containers
remove_dynamic_containers
