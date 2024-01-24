#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
#
#   Copyright (C) 2021-Present SKALE Labs
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

import distro
import functools
import logging
from typing import Dict

from node_cli.cli.info import VERSION
from node_cli.configs import CONTAINER_CONFIG_PATH, CONTAINER_CONFIG_TMP_PATH
from node_cli.core.host import ensure_btrfs_kernel_module_autoloaded, link_env_file, prepare_host

from node_cli.core.docker_config import configure_docker
from node_cli.core.nginx import generate_nginx_config
from node_cli.core.node_options import NodeOptions
from node_cli.core.resources import update_resource_allocation, init_shared_space_volume

from node_cli.operations.common import (
    backup_old_contracts,
    download_contracts,
    configure_filebeat,
    configure_flask,
    unpack_backup_archive
)
from node_cli.operations.volume import (
    cleanup_volume_artifacts,
    ensure_filestorage_mapping,
    prepare_block_device
)
from node_cli.operations.docker_lvmpy import lvmpy_install  # noqa
from node_cli.operations.skale_node import download_skale_node, sync_skale_node, update_images
from node_cli.core.checks import CheckType, run_checks as run_host_checks
from node_cli.core.iptables import configure_iptables
from node_cli.utils.docker_utils import (
    compose_rm,
    compose_up,
    compose_up_sync,
    docker_cleanup,
    remove_dynamic_containers
)
from node_cli.utils.meta import get_meta_info, update_meta
from node_cli.utils.print_formatters import print_failed_requirements_checks


logger = logging.getLogger(__name__)


def checked_host(func):
    @functools.wraps(func)
    def wrapper(env_filepath: str, env: Dict, *args, **kwargs):
        download_skale_node(
            env['CONTAINER_CONFIGS_STREAM'],
            env.get('CONTAINER_CONFIGS_DIR')
        )
        failed_checks = run_host_checks(
            env['DISK_MOUNTPOINT'],
            env['ENV_TYPE'],
            CONTAINER_CONFIG_TMP_PATH,
            check_type=CheckType.PREINSTALL
        )
        if failed_checks:
            print_failed_requirements_checks(failed_checks)
            return False

        result = func(env_filepath, env, *args, **kwargs)
        if not result:
            return result

        failed_checks = run_host_checks(
            env['DISK_MOUNTPOINT'],
            env['ENV_TYPE'],
            CONTAINER_CONFIG_PATH,
            check_type=CheckType.POSTINSTALL
        )
        if failed_checks:
            print_failed_requirements_checks(failed_checks)
            return False
        return True

    return wrapper


@checked_host
def update(env_filepath: str, env: Dict) -> None:
    compose_rm(env)
    remove_dynamic_containers()

    sync_skale_node()

    ensure_btrfs_kernel_module_autoloaded()

    if env.get('SKIP_DOCKER_CONFIG') != 'True':
        configure_docker()

    backup_old_contracts()
    download_contracts(env)

    lvmpy_install(env)
    generate_nginx_config()

    prepare_host(
        env_filepath,
        env['ENV_TYPE'],
        allocation=True
    )
    init_shared_space_volume(env['ENV_TYPE'])

    current_stream = get_meta_info().config_stream
    skip_cleanup = env.get('SKIP_DOCKER_CLEANUP') == 'True'
    if not skip_cleanup and current_stream != env['CONTAINER_CONFIGS_STREAM']:
        logger.info(
            'Stream version was changed from %s to %s',
            current_stream,
            env['CONTAINER_CONFIGS_STREAM']
        )
        docker_cleanup()

    update_meta(
        VERSION,
        env['CONTAINER_CONFIGS_STREAM'],
        env['DOCKER_LVMPY_STREAM'],
        distro.id(),
        distro.version()
    )
    update_images(env.get('CONTAINER_CONFIGS_DIR') != '')
    compose_up(env)
    return True


@checked_host
def init(env_filepath: str, env: dict) -> bool:
    sync_skale_node()

    ensure_btrfs_kernel_module_autoloaded()
    if env.get('SKIP_DOCKER_CONFIG') != 'True':
        configure_docker()

    prepare_host(
        env_filepath,
        env_type=env['ENV_TYPE']
    )
    link_env_file()
    download_contracts(env)

    configure_filebeat()
    configure_flask()
    configure_iptables()
    generate_nginx_config()

    lvmpy_install(env)
    init_shared_space_volume(env['ENV_TYPE'])

    update_meta(
        VERSION,
        env['CONTAINER_CONFIGS_STREAM'],
        env['DOCKER_LVMPY_STREAM'],
        distro.id(),
        distro.version()
    )
    update_resource_allocation(env_type=env['ENV_TYPE'])
    update_images(env.get('CONTAINER_CONFIGS_DIR') != '')
    compose_up(env)
    return True


def init_sync(
    env_filepath: str,
    env: dict,
    archive: bool,
    catchup: bool,
    historic_state: bool
) -> bool:
    cleanup_volume_artifacts(env['DISK_MOUNTPOINT'])
    download_skale_node(
        env.get('CONTAINER_CONFIGS_STREAM'),
        env.get('CONTAINER_CONFIGS_DIR')
    )
    sync_skale_node()

    if env.get('SKIP_DOCKER_CONFIG') != 'True':
        configure_docker()

    prepare_host(
        env_filepath,
        env_type=env['ENV_TYPE'],
    )

    node_options = NodeOptions()
    node_options.archive = archive
    node_options.catchup = catchup
    node_options.historic_state = historic_state

    ensure_filestorage_mapping()
    link_env_file()
    download_contracts(env)

    generate_nginx_config()
    prepare_block_device(
        env['DISK_MOUNTPOINT'],
        force=env['ENFORCE_BTRFS'] == 'True'
    )

    update_meta(
        VERSION,
        env['CONTAINER_CONFIGS_STREAM'],
        env['DOCKER_LVMPY_STREAM'],
        distro.id(),
        distro.version()
    )
    update_resource_allocation(env_type=env['ENV_TYPE'])
    update_images(env.get('CONTAINER_CONFIGS_DIR') != '', sync_node=True)
    compose_up_sync(env)
    return True


def update_sync(env_filepath: str, env: Dict) -> bool:
    compose_rm(env, sync_node=True)
    remove_dynamic_containers()
    cleanup_volume_artifacts(env['DISK_MOUNTPOINT'])
    download_skale_node(
        env['CONTAINER_CONFIGS_STREAM'],
        env.get('CONTAINER_CONFIGS_DIR')
    )
    sync_skale_node()

    if env.get('SKIP_DOCKER_CONFIG') != 'True':
        configure_docker()

    ensure_filestorage_mapping()
    backup_old_contracts()
    download_contracts(env)

    prepare_block_device(
        env['DISK_MOUNTPOINT'],
        force=env['ENFORCE_BTRFS'] == 'True'
    )
    generate_nginx_config()

    prepare_host(
        env_filepath,
        env['ENV_TYPE'],
        allocation=True
    )

    update_meta(
        VERSION,
        env['CONTAINER_CONFIGS_STREAM'],
        env['DOCKER_LVMPY_STREAM'],
        distro.id(),
        distro.version()
    )
    update_images(env.get('CONTAINER_CONFIGS_DIR') != '', sync_node=True)
    compose_up_sync(env)
    return True


def turn_off():
    logger.info('Turning off the node...')
    compose_rm()
    remove_dynamic_containers()
    logger.info('Node was successfully turned off')


def turn_on(env):
    logger.info('Turning on the node...')
    compose_up(env)


def restore(env, backup_path, config_only=False):
    unpack_backup_archive(backup_path)
    failed_checks = run_host_checks(
        env['DISK_MOUNTPOINT'],
        env['ENV_TYPE'],
        CONTAINER_CONFIG_PATH,
        check_type=CheckType.PREINSTALL
    )
    if failed_checks:
        print_failed_requirements_checks(failed_checks)
        return False

    ensure_btrfs_kernel_module_autoloaded()
    if env.get('SKIP_DOCKER_CONFIG') != 'True':
        configure_docker()

    link_env_file()
    configure_iptables()
    lvmpy_install(env)
    init_shared_space_volume(env['ENV_TYPE'])

    update_meta(
        VERSION,
        env['CONTAINER_CONFIGS_STREAM'],
        env['DOCKER_LVMPY_STREAM'],
        distro.id(),
        distro.version()
    )
    update_resource_allocation(env_type=env['ENV_TYPE'])
    if not config_only:
        compose_up(env)

    failed_checks = run_host_checks(
        env['DISK_MOUNTPOINT'],
        env['ENV_TYPE'],
        CONTAINER_CONFIG_PATH,
        check_type=CheckType.POSTINSTALL
    )
    if failed_checks:
        print_failed_requirements_checks(failed_checks)
        return False
    return True
