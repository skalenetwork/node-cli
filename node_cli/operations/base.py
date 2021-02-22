#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
#
#   Copyright (C) 2021 SKALE Labs
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

from node_cli.cli.info import VERSION
from node_cli.core.host import prepare_host, link_env_file
from node_cli.core.resources import update_resource_allocation

from node_cli.operations.common import (
    backup_old_contracts, download_contracts, download_filestorage_artifacts, configure_filebeat,
    configure_flask, configure_iptables
)
from node_cli.operations.docker_lvmpy import docker_lvmpy_update, docker_lvmpy_install
from node_cli.operations.skale_node import init_skale_node_repo, update_skale_node_repo

from node_cli.utils.docker_utils import compose_rm, compose_up, remove_dynamic_containers
from node_cli.utils.meta import update_meta


def update(env_filepath: str, env: str) -> None:
    compose_rm(env)
    remove_dynamic_containers()

    backup_old_contracts()
    download_contracts(env)
    download_filestorage_artifacts()
    docker_lvmpy_update(env)
    update_skale_node_repo(env)

    prepare_host(
        env_filepath,
        env['DISK_MOUNTPOINT'],
        env['SGX_SERVER_URL'],
        allocation=True
    )
    update_meta(VERSION, env['CONTAINER_CONFIGS_STREAM'])
    compose_up(env)


def init(env_filepath: str, env: str) -> None:
    init_skale_node_repo(env)
    # todo: add hardware checks
    prepare_host(
        env_filepath,
        env['DISK_MOUNTPOINT'],
        env['SGX_SERVER_URL']
    )
    link_env_file()
    download_contracts(env)
    download_filestorage_artifacts()

    configure_filebeat()
    configure_flask()
    configure_iptables()

    docker_lvmpy_install(env)

    update_meta(VERSION, env['CONTAINER_CONFIGS_STREAM'])
    update_resource_allocation()
    compose_up(env)


def backup_init(env):
    pass


def turn_off(env):
    pass


def turn_on(env):
    pass
