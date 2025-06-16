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

import time

import distro
import functools
import logging
from typing import Dict, Optional

from node_cli.configs import (
    CONTAINER_CONFIG_PATH,
    CONTAINER_CONFIG_TMP_PATH,
    SKALE_DIR,
    GLOBAL_SKALE_DIR,
)
from node_cli.core.checks import CheckType, run_checks as run_host_checks
from node_cli.core.docker_config import configure_docker
from node_cli.core.host import (
    ensure_btrfs_kernel_module_autoloaded,
    link_env_file,
    prepare_host,
)
from node_cli.core.nftables import configure_nftables
from node_cli.core.nginx import generate_nginx_config
from node_cli.core.node_options import NodeOptions
from node_cli.core.resources import update_resource_allocation, init_shared_space_volume
from node_cli.core.schains import (
    update_node_cli_schain_status,
    cleanup_sync_datadir,
)
from node_cli.cli.info import VERSION, TYPE
from node_cli.operations.common import configure_filebeat, configure_flask, unpack_backup_archive
from node_cli.operations.docker_lvmpy import lvmpy_install
from node_cli.operations.config_repo import (
    download_skale_node,
    sync_skale_node,
    update_images,
)
from node_cli.operations.volume import (
    cleanup_volume_artifacts,
    ensure_filestorage_mapping,
    prepare_block_device,
)
from node_cli.utils.docker_utils import (
    compose_rm,
    compose_up,
    docker_cleanup,
    remove_dynamic_containers,
)
from node_cli.utils.helper import str_to_bool, rm_dir
from node_cli.utils.meta import CliMetaManager, MirageCliMetaManager
from node_cli.utils.node_type import NodeType
from node_cli.utils.print_formatters import print_failed_requirements_checks


logger = logging.getLogger(__name__)


def checked_host(func):
    @functools.wraps(func)
    def wrapper(env_filepath: str, env: Dict, *args, **kwargs):
        download_skale_node(env.get('CONTAINER_CONFIGS_STREAM'), env.get('CONTAINER_CONFIGS_DIR'))
        failed_checks = run_host_checks(
            env['DISK_MOUNTPOINT'],
            TYPE,
            env['ENV_TYPE'],
            CONTAINER_CONFIG_TMP_PATH,
            check_type=CheckType.PREINSTALL,
        )
        if failed_checks:
            print_failed_requirements_checks(failed_checks)
            return False

        result = func(env_filepath, env, *args, **kwargs)
        if not result:
            return result

        failed_checks = run_host_checks(
            env['DISK_MOUNTPOINT'],
            TYPE,
            env['ENV_TYPE'],
            CONTAINER_CONFIG_PATH,
            check_type=CheckType.POSTINSTALL,
        )
        if failed_checks:
            print_failed_requirements_checks(failed_checks)
            return False
        return True

    return wrapper


@checked_host
def update(env_filepath: str, env: Dict, node_type: NodeType) -> bool:
    compose_rm(node_type=node_type, env=env)
    remove_dynamic_containers()

    sync_skale_node()
    ensure_btrfs_kernel_module_autoloaded()

    if env.get('SKIP_DOCKER_CONFIG') != 'True':
        configure_docker()

    enable_monitoring = str_to_bool(env.get('MONITORING_CONTAINERS', 'False'))
    configure_nftables(enable_monitoring=enable_monitoring)

    lvmpy_install(env)
    generate_nginx_config()

    prepare_host(env_filepath, env['ENV_TYPE'], allocation=True)
    init_shared_space_volume(env['ENV_TYPE'])

    meta_manager = CliMetaManager()
    current_stream = meta_manager.get_meta_info().config_stream
    skip_cleanup = env.get('SKIP_DOCKER_CLEANUP') == 'True'
    if not skip_cleanup and current_stream != env['CONTAINER_CONFIGS_STREAM']:
        logger.info(
            'Stream version was changed from %s to %s',
            current_stream,
            env['CONTAINER_CONFIGS_STREAM'],
        )
        docker_cleanup()

    meta_manager.update_meta(
        VERSION,
        env['CONTAINER_CONFIGS_STREAM'],
        env['DOCKER_LVMPY_STREAM'],
        distro.id(),
        distro.version(),
    )
    update_images(env=env, node_type=node_type)
    compose_up(env=env, node_type=node_type)
    return True


@checked_host
def migrate_mirage_boot(env_filepath: str, env: Dict) -> bool:
    compose_rm(node_type=NodeType.MIRAGE, env=env)
    cleanup_volume_artifacts(env['DISK_MOUNTPOINT'])

    sync_skale_node()
    ensure_btrfs_kernel_module_autoloaded()

    if env.get('SKIP_DOCKER_CONFIG') != 'True':
        configure_docker()

    enable_monitoring = str_to_bool(env.get('MONITORING_CONTAINERS', 'False'))
    configure_nftables(enable_monitoring=enable_monitoring)

    generate_nginx_config()

    prepare_host(env_filepath, env['ENV_TYPE'])

    meta_manager = CliMetaManager()
    current_stream = meta_manager.get_meta_info().config_stream
    skip_cleanup = env.get('SKIP_DOCKER_CLEANUP') == 'True'
    if not skip_cleanup and current_stream != env['CONTAINER_CONFIGS_STREAM']:
        logger.info(
            'Stream version was changed from %s to %s',
            current_stream,
            env['CONTAINER_CONFIGS_STREAM'],
        )
        docker_cleanup()

    meta_manager.update_meta(
        VERSION,
        env['CONTAINER_CONFIGS_STREAM'],
        None,
        distro.id(),
        distro.version(),
    )
    update_images(env=env, node_type=NodeType.MIRAGE)
    compose_up(env=env, node_type=NodeType.MIRAGE)
    return True


@checked_host
def update_mirage_boot(env_filepath: str, env: Dict) -> bool:
    compose_rm(node_type=NodeType.MIRAGE, env=env)
    remove_dynamic_containers()
    cleanup_volume_artifacts(env['DISK_MOUNTPOINT'])

    sync_skale_node()
    ensure_btrfs_kernel_module_autoloaded()

    if env.get('SKIP_DOCKER_CONFIG') != 'True':
        configure_docker()

    enable_monitoring = str_to_bool(env.get('MONITORING_CONTAINERS', 'False'))
    configure_nftables(enable_monitoring=enable_monitoring)

    generate_nginx_config()
    prepare_block_device(env['DISK_MOUNTPOINT'], force=env['ENFORCE_BTRFS'] == 'True')

    prepare_host(env_filepath, env['ENV_TYPE'])

    meta_manager = MirageCliMetaManager()
    current_stream = meta_manager.get_meta_info().config_stream
    skip_cleanup = env.get('SKIP_DOCKER_CLEANUP') == 'True'
    if not skip_cleanup and current_stream != env['CONTAINER_CONFIGS_STREAM']:
        logger.info(
            'Stream version was changed from %s to %s',
            current_stream,
            env['CONTAINER_CONFIGS_STREAM'],
        )
        docker_cleanup()

    meta_manager.update_meta(
        VERSION,
        env['CONTAINER_CONFIGS_STREAM'],
        distro.id(),
        distro.version(),
    )
    update_images(env=env, node_type=NodeType.MIRAGE)
    compose_up(env=env, node_type=NodeType.MIRAGE, is_mirage_boot=True)
    return True


@checked_host
def init(env_filepath: str, env: dict, node_type: NodeType) -> None:
    sync_skale_node()

    ensure_btrfs_kernel_module_autoloaded()
    if env.get('SKIP_DOCKER_CONFIG') != 'True':
        configure_docker()

    enable_monitoring = str_to_bool(env.get('MONITORING_CONTAINERS', 'False'))
    configure_nftables(enable_monitoring=enable_monitoring)

    prepare_host(env_filepath, env_type=env['ENV_TYPE'])
    link_env_file()

    configure_filebeat()
    configure_flask()
    generate_nginx_config()

    lvmpy_install(env)
    init_shared_space_volume(env['ENV_TYPE'])

    meta_manager = CliMetaManager()
    meta_manager.update_meta(
        VERSION,
        env['CONTAINER_CONFIGS_STREAM'],
        env['DOCKER_LVMPY_STREAM'],
        distro.id(),
        distro.version(),
    )
    update_resource_allocation(env_type=env['ENV_TYPE'])
    update_images(env=env, node_type=node_type)

    compose_up(env=env, node_type=node_type)


@checked_host
def init_mirage_boot(env_filepath: str, env: dict) -> None:
    sync_skale_node()
    cleanup_volume_artifacts(env['DISK_MOUNTPOINT'])

    ensure_btrfs_kernel_module_autoloaded()
    if env.get('SKIP_DOCKER_CONFIG') != 'True':
        configure_docker()

    enable_monitoring = str_to_bool(env.get('MONITORING_CONTAINERS', 'False'))
    configure_nftables(enable_monitoring=enable_monitoring)

    prepare_host(env_filepath, env_type=env['ENV_TYPE'])
    link_env_file()

    configure_filebeat()
    configure_flask()
    generate_nginx_config()
    prepare_block_device(env['DISK_MOUNTPOINT'], force=env['ENFORCE_BTRFS'] == 'True')

    meta_manager = CliMetaManager()
    meta_manager.update_meta(
        VERSION,
        env['CONTAINER_CONFIGS_STREAM'],
        None,
        distro.id(),
        distro.version(),
    )
    update_images(env=env, node_type=NodeType.MIRAGE)

    compose_up(env=env, node_type=NodeType.MIRAGE, is_mirage_boot=True)


def init_sync(
    env_filepath: str,
    env: dict,
    indexer: bool,
    archive: bool,
    snapshot: bool,
    snapshot_from: Optional[str],
) -> None:
    cleanup_volume_artifacts(env['DISK_MOUNTPOINT'])
    download_skale_node(env.get('CONTAINER_CONFIGS_STREAM'), env.get('CONTAINER_CONFIGS_DIR'))
    sync_skale_node()

    if env.get('SKIP_DOCKER_CONFIG') != 'True':
        configure_docker()

    enable_monitoring = str_to_bool(env.get('MONITORING_CONTAINERS', 'False'))
    configure_nftables(enable_monitoring=enable_monitoring)

    prepare_host(
        env_filepath,
        env_type=env['ENV_TYPE'],
    )

    node_options = NodeOptions()
    node_options.archive = archive or indexer
    node_options.catchup = archive or indexer
    node_options.historic_state = archive

    ensure_filestorage_mapping()
    link_env_file()

    generate_nginx_config()
    prepare_block_device(env['DISK_MOUNTPOINT'], force=env['ENFORCE_BTRFS'] == 'True')

    meta_manager = CliMetaManager()
    meta_manager.update_meta(
        VERSION,
        env['CONTAINER_CONFIGS_STREAM'],
        None,
        distro.id(),
        distro.version(),
    )
    update_resource_allocation(env_type=env['ENV_TYPE'])

    schain_name = env['SCHAIN_NAME']
    if snapshot or snapshot_from:
        ts = int(time.time())
        update_node_cli_schain_status(schain_name, repair_ts=ts, snapshot_from=snapshot_from)

    update_images(env=env, node_type=NodeType.SYNC)

    compose_up(env=env, node_type=NodeType.SYNC)


def update_sync(env_filepath: str, env: Dict) -> bool:
    compose_rm(env=env, node_type=NodeType.SYNC)
    remove_dynamic_containers()
    cleanup_volume_artifacts(env['DISK_MOUNTPOINT'])
    download_skale_node(env['CONTAINER_CONFIGS_STREAM'], env.get('CONTAINER_CONFIGS_DIR'))
    sync_skale_node()

    if env.get('SKIP_DOCKER_CONFIG') != 'True':
        configure_docker()

    enable_monitoring = str_to_bool(env.get('MONITORING_CONTAINERS', 'False'))
    configure_nftables(enable_monitoring=enable_monitoring)

    ensure_filestorage_mapping()

    prepare_block_device(env['DISK_MOUNTPOINT'], force=env['ENFORCE_BTRFS'] == 'True')
    generate_nginx_config()

    prepare_host(env_filepath, env['ENV_TYPE'], allocation=True)

    meta_manager = CliMetaManager()
    meta_manager.update_meta(
        VERSION,
        env['CONTAINER_CONFIGS_STREAM'],
        env['DOCKER_LVMPY_STREAM'],
        distro.id(),
        distro.version(),
    )
    update_images(env=env, node_type=NodeType.SYNC)

    compose_up(env=env, node_type=NodeType.SYNC)
    return True


def turn_off(env: dict, node_type: NodeType) -> None:
    logger.info('Turning off the node...')
    compose_rm(env=env, node_type=node_type)
    remove_dynamic_containers()
    logger.info('Node was successfully turned off')


def turn_on(env: dict, node_type: NodeType) -> None:
    logger.info('Turning on the node...')
    meta_manager = CliMetaManager()
    meta_manager.update_meta(
        VERSION,
        env['CONTAINER_CONFIGS_STREAM'],
        env['DOCKER_LVMPY_STREAM'],
        distro.id(),
        distro.version(),
    )
    if env.get('SKIP_DOCKER_CONFIG') != 'True':
        configure_docker()

    enable_monitoring = str_to_bool(env.get('MONITORING_CONTAINERS', 'False'))
    configure_nftables(enable_monitoring=enable_monitoring)

    logger.info('Launching containers on the node...')
    compose_up(env=env, node_type=node_type)


def restore(env, backup_path, node_type: NodeType, config_only=False):
    unpack_backup_archive(backup_path)
    failed_checks = run_host_checks(
        env['DISK_MOUNTPOINT'],
        TYPE,
        env['ENV_TYPE'],
        CONTAINER_CONFIG_PATH,
        check_type=CheckType.PREINSTALL,
    )
    if failed_checks:
        print_failed_requirements_checks(failed_checks)
        return False

    ensure_btrfs_kernel_module_autoloaded()

    if env.get('SKIP_DOCKER_CONFIG') != 'True':
        configure_docker()

    enable_monitoring = str_to_bool(env.get('MONITORING_CONTAINERS', 'False'))
    configure_nftables(enable_monitoring=enable_monitoring)

    link_env_file()
    lvmpy_install(env)
    init_shared_space_volume(env['ENV_TYPE'])

    meta_manager = CliMetaManager()
    meta_manager.update_meta(
        VERSION,
        env['CONTAINER_CONFIGS_STREAM'],
        env['DOCKER_LVMPY_STREAM'],
        distro.id(),
        distro.version(),
    )
    if not config_only:
        compose_up(env=env, node_type=node_type)

    failed_checks = run_host_checks(
        env['DISK_MOUNTPOINT'],
        TYPE,
        env['ENV_TYPE'],
        CONTAINER_CONFIG_PATH,
        check_type=CheckType.POSTINSTALL,
    )
    if failed_checks:
        print_failed_requirements_checks(failed_checks)
        return False
    return True


def cleanup_sync(env, schain_name: str) -> None:
    turn_off(env, node_type=NodeType.SYNC)
    cleanup_sync_datadir(schain_name=schain_name)
    rm_dir(GLOBAL_SKALE_DIR)
    rm_dir(SKALE_DIR)
