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

import logging

from node_cli.cli.info import VERSION
from node_cli.core.host import ( # noqa - tmp!
    prepare_host, link_env_file, run_preinstall_checks
)
from node_cli.core.resources import update_resource_allocation

from node_cli.operations.common import (
    backup_old_contracts, download_contracts, download_filestorage_artifacts, configure_filebeat,
    configure_flask, unpack_backup_archive
)
from node_cli.operations.docker_lvmpy import docker_lvmpy_update, docker_lvmpy_install
from node_cli.operations.skale_node import sync_skale_node, update_images

from node_cli.core.iptables import configure_iptables
from node_cli.utils.docker_utils import compose_rm, compose_up, remove_dynamic_containers
from node_cli.utils.meta import update_meta
from node_cli.utils.print_formatters import print_failed_requirements_checks # noqa - tmp!


logger = logging.getLogger(__name__)


def update(env_filepath: str, env: str) -> None:
    compose_rm(env)
    remove_dynamic_containers()

    backup_old_contracts()
    download_contracts(env)
    download_filestorage_artifacts()
    docker_lvmpy_update(env)
    sync_skale_node(env)

    prepare_host(
        env_filepath,
        env['DISK_MOUNTPOINT'],
        env['SGX_SERVER_URL'],
        env['ENV_TYPE'],
        allocation=True
    )
    update_meta(
        VERSION,
        env['CONTAINER_CONFIGS_STREAM'],
        env['DOCKER_LVMPY_STREAM']
    )
    update_images(env)
    compose_up(env)


def init(env_filepath: str, env: str) -> bool:
    sync_skale_node(env)
    # failed_checks = run_preinstall_checks(env['ENV_TYPE'])
    # if failed_checks:
    #     print_failed_requirements_checks(failed_checks)
    #     return False
    prepare_host(
        env_filepath,
        env['DISK_MOUNTPOINT'],
        env['SGX_SERVER_URL'],
        env_type=env['ENV_TYPE'],
    )
    link_env_file()
    download_contracts(env)
    download_filestorage_artifacts()

    configure_filebeat()
    configure_flask()
    configure_iptables()

    docker_lvmpy_install(env)

    update_meta(
        VERSION,
        env['CONTAINER_CONFIGS_STREAM'],
        env['DOCKER_LVMPY_STREAM']
    )
    update_resource_allocation(env_type=env['ENV_TYPE'])
    update_images(env)
    compose_up(env)
    return True


def turn_off():
    logger.info('Turning off the node...')
    compose_rm()
    remove_dynamic_containers()
    logger.info('Node was successfully turned off')


def turn_on(env):
    logger.info('Turning on the node...')
    compose_up(env)


def restore(env, backup_path):
    unpack_backup_archive(backup_path)
    link_env_file()
    configure_iptables()
    docker_lvmpy_install(env)
    update_meta(
        VERSION,
        env['CONTAINER_CONFIGS_STREAM'],
        env['DOCKER_LVMPY_STREAM']
    )
    update_resource_allocation(env_type=env['ENV_TYPE'])
    compose_up(env)
