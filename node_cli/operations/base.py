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
from node_cli.core.host import prepare_host
from node_cli.operations.common import (
    remove_dynamic_containers, backup_old_contracts, download_contracts, docker_lvmpy_update,
    update_skale_node, download_filestorage_artifacts
)
from node_cli.utils.docker_utils import compose_rm, compose_up
from node_cli.utils.meta import update_meta


def update(env_filepath: str, env: str) -> None:
    compose_rm(env)
    remove_dynamic_containers()

    backup_old_contracts()
    download_contracts(env)
    docker_lvmpy_update(env)
    update_skale_node(env)

    prepare_host(
        env_filepath,
        env['DISK_MOUNTPOINT'],
        env['SGX_SERVER_URL'],
        allocation=True
    )
    update_meta(VERSION, env['CONTAINER_CONFIGS_STREAM'])
    download_filestorage_artifacts()
    compose_up(env)


def init(env):
    pass


def backup_init(env):
    pass


def turn_off(env):
    pass


def turn_on(env):
    pass
