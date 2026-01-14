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

import functools
import logging
import time
from typing import Dict, Optional

import distro

from node_cli.cli.info import TYPE, VERSION
from node_cli.configs import (
    CONTAINER_CONFIG_PATH,
    CONTAINER_CONFIG_TMP_PATH,
    GLOBAL_SKALE_DIR,
    NFTABLES_CHAIN_FOLDER_PATH,
    SKALE_DIR,
)
from node_cli.core.checks import CheckType
from node_cli.core.checks import run_checks as run_host_checks
from node_cli.core.docker_config import cleanup_docker_configuration, configure_docker
from node_cli.core.host import (
    ensure_btrfs_kernel_module_autoloaded,
    link_env_file,
    prepare_host,
)
from node_cli.core.nftables import configure_nftables
from node_cli.core.nginx import generate_nginx_config
from node_cli.core.node_options import (
    mark_active_node,
    set_passive_node_options,
    upsert_node_mode,
)
from node_cli.core.resources import init_shared_space_volume, update_resource_allocation
from node_cli.core.schains import (
    cleanup_lvm_datadir,
    cleanup_no_lvm_datadir,
    update_node_cli_schain_status,
)
from node_cli.operations.common import configure_filebeat, configure_flask, unpack_backup_archive
from node_cli.operations.config_repo import (
    download_skale_node,
    sync_skale_node,
    update_images,
)
from node_cli.operations.docker_lvmpy import lvmpy_install
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
    system_prune,
)
from node_cli.utils.helper import cleanup_dir_content, rm_dir, str_to_bool
from node_cli.utils.meta import CliMetaManager, FairCliMetaManager
from node_cli.utils.node_type import NodeMode, NodeType
from node_cli.utils.print_formatters import print_failed_requirements_checks

logger = logging.getLogger(__name__)


def checked_host(func):
    @functools.wraps(func)
    def wrapper(env_filepath: str, env: Dict, node_mode: NodeMode, *args, **kwargs):
        download_skale_node(env.get('NODE_VERSION'), env.get('CONTAINER_CONFIGS_DIR'))
        failed_checks = run_host_checks(
            env['BLOCK_DEVICE'],
            TYPE,
            node_mode,
            env['ENV_TYPE'],
            CONTAINER_CONFIG_TMP_PATH,
            check_type=CheckType.PREINSTALL,
        )
        if failed_checks:
            print_failed_requirements_checks(failed_checks)
            return False

        result = func(env_filepath, env, node_mode, *args, **kwargs)
        if not result:
            return result

        failed_checks = run_host_checks(
            env['BLOCK_DEVICE'],
            TYPE,
            node_mode,
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
def update(env_filepath: str, env: Dict, node_mode: NodeMode) -> bool:
    compose_rm(node_type=NodeType.SKALE, node_mode=node_mode, env=env)
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
    if not skip_cleanup and current_stream != env['NODE_VERSION']:
        logger.info(
            'Stream version was changed from %s to %s',
            current_stream,
            env['NODE_VERSION'],
        )
        docker_cleanup()

    meta_manager.update_meta(
        VERSION,
        env['NODE_VERSION'],
        env['DOCKER_LVMPY_VERSION'],
        distro.id(),
        distro.version(),
    )
    update_images(env=env, node_type=NodeType.SKALE, node_mode=node_mode)
    compose_up(env=env, node_type=NodeType.SKALE, node_mode=node_mode)
    return True


@checked_host
def init(env_filepath: str, env: dict, node_mode: NodeMode) -> None:
    sync_skale_node()
    ensure_btrfs_kernel_module_autoloaded()
    if env.get('SKIP_DOCKER_CONFIG') != 'True':
        configure_docker()

    enable_monitoring = str_to_bool(env.get('MONITORING_CONTAINERS', 'False'))
    configure_nftables(enable_monitoring=enable_monitoring)

    prepare_host(env_filepath, env_type=env['ENV_TYPE'])
    link_env_file()

    mark_active_node()

    configure_filebeat()
    configure_flask()
    generate_nginx_config()

    lvmpy_install(env)
    init_shared_space_volume(env['ENV_TYPE'])

    meta_manager = CliMetaManager()
    meta_manager.update_meta(
        VERSION,
        env['NODE_VERSION'],
        env['DOCKER_LVMPY_VERSION'],
        distro.id(),
        distro.version(),
    )
    update_resource_allocation(env_type=env['ENV_TYPE'])
    update_images(env=env, node_type=NodeType.SKALE, node_mode=node_mode)
    compose_up(env=env, node_type=NodeType.SKALE, node_mode=node_mode)


def init_passive(
    env_filepath: str,
    env: dict,
    indexer: bool,
    archive: bool,
    snapshot: bool,
    snapshot_from: Optional[str],
) -> None:
    cleanup_volume_artifacts(env['BLOCK_DEVICE'])
    download_skale_node(env.get('NODE_VERSION'), env.get('CONTAINER_CONFIGS_DIR'))
    sync_skale_node()

    if env.get('SKIP_DOCKER_CONFIG') != 'True':
        configure_docker()

    enable_monitoring = str_to_bool(env.get('MONITORING_CONTAINERS', 'False'))
    configure_nftables(enable_monitoring=enable_monitoring)

    prepare_host(
        env_filepath,
        env_type=env['ENV_TYPE'],
    )
    failed_checks = run_host_checks(
        env['BLOCK_DEVICE'],
        TYPE,
        NodeMode.PASSIVE,
        env['ENV_TYPE'],
        CONTAINER_CONFIG_PATH,
        check_type=CheckType.PREINSTALL
    )
    if failed_checks:
        print_failed_requirements_checks(failed_checks)

    set_passive_node_options(archive=archive, indexer=indexer)

    ensure_filestorage_mapping()
    link_env_file()

    generate_nginx_config()
    prepare_block_device(env['BLOCK_DEVICE'], force=env['ENFORCE_BTRFS'] == 'True')

    meta_manager = CliMetaManager()
    meta_manager.update_meta(
        VERSION,
        env['NODE_VERSION'],
        None,
        distro.id(),
        distro.version(),
    )
    update_resource_allocation(env_type=env['ENV_TYPE'])

    schain_name = env['SCHAIN_NAME']
    if snapshot or snapshot_from:
        ts = int(time.time())
        update_node_cli_schain_status(schain_name, repair_ts=ts, snapshot_from=snapshot_from)

    update_images(env=env, node_type=NodeType.SKALE, node_mode=NodeMode.PASSIVE)
    compose_up(env=env, node_type=NodeType.SKALE, node_mode=NodeMode.PASSIVE)


def update_passive(env_filepath: str, env: Dict) -> bool:
    compose_rm(env=env, node_type=NodeType.SKALE, node_mode=NodeMode.PASSIVE)
    remove_dynamic_containers()
    cleanup_volume_artifacts(env['BLOCK_DEVICE'])
    download_skale_node(env['NODE_VERSION'], env.get('CONTAINER_CONFIGS_DIR'))
    sync_skale_node()

    if env.get('SKIP_DOCKER_CONFIG') != 'True':
        configure_docker()

    enable_monitoring = str_to_bool(env.get('MONITORING_CONTAINERS', 'False'))
    configure_nftables(enable_monitoring=enable_monitoring)

    ensure_filestorage_mapping()

    prepare_block_device(env['BLOCK_DEVICE'], force=env['ENFORCE_BTRFS'] == 'True')
    generate_nginx_config()

    prepare_host(env_filepath, env['ENV_TYPE'], allocation=True)

    failed_checks = run_host_checks(
        env['BLOCK_DEVICE'],
        TYPE,
        NodeMode.PASSIVE,
        env['ENV_TYPE'],
        CONTAINER_CONFIG_PATH,
        check_type=CheckType.PREINSTALL
    )
    if failed_checks:
        print_failed_requirements_checks(failed_checks)

    meta_manager = CliMetaManager()
    meta_manager.update_meta(
        VERSION,
        env['NODE_VERSION'],
        None,
        distro.id(),
        distro.version(),
    )
    update_images(env=env, node_type=NodeType.SKALE, node_mode=NodeMode.PASSIVE)
    compose_up(env=env, node_type=NodeType.SKALE, node_mode=NodeMode.PASSIVE)
    return True


def turn_off(env: dict, node_type: NodeType, node_mode: NodeMode) -> None:
    logger.info('Turning off the node...')
    compose_rm(env=env, node_type=node_type, node_mode=node_mode)
    remove_dynamic_containers()
    logger.info('Node was successfully turned off')


def turn_on(env: dict, node_type: NodeType, node_mode: NodeMode) -> None:
    logger.info('Turning on the node...')
    if node_type == NodeType.FAIR:
        meta_manager = FairCliMetaManager()
        meta_manager.update_meta(
            VERSION,
            env['NODE_VERSION'],
            distro.id(),
            distro.version(),
        )
    else:
        meta_manager = CliMetaManager()
        meta_manager.update_meta(
            VERSION, env['NODE_VERSION'], env['DOCKER_LVMPY_VERSION'], distro.id(), distro.version()
        )
    if env.get('SKIP_DOCKER_CONFIG') != 'True':
        configure_docker()

    enable_monitoring = str_to_bool(env.get('MONITORING_CONTAINERS', 'False'))
    configure_nftables(enable_monitoring=enable_monitoring)

    logger.info('Launching containers on the node...')
    compose_up(env=env, node_type=node_type, node_mode=node_mode)


def restore(env, backup_path, node_type: NodeType, config_only=False):
    node_mode = upsert_node_mode(node_mode=NodeMode.ACTIVE)
    unpack_backup_archive(backup_path)
    failed_checks = run_host_checks(
        env['BLOCK_DEVICE'],
        TYPE,
        node_mode,
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
        env['NODE_VERSION'],
        env['DOCKER_LVMPY_VERSION'],
        distro.id(),
        distro.version(),
    )
    if not config_only:
        compose_up(env=env, node_type=node_type, node_mode=node_mode)

    failed_checks = run_host_checks(
        env['BLOCK_DEVICE'],
        TYPE,
        node_mode,
        env['ENV_TYPE'],
        CONTAINER_CONFIG_PATH,
        check_type=CheckType.POSTINSTALL,
    )
    if failed_checks:
        print_failed_requirements_checks(failed_checks)
        return False
    return True


def cleanup_passive(env, schain_name: str) -> None:
    turn_off(env, node_type=NodeType.SKALE, node_mode=NodeMode.PASSIVE)
    cleanup_no_lvm_datadir(chain_name=schain_name)
    rm_dir(GLOBAL_SKALE_DIR)
    rm_dir(SKALE_DIR)


def cleanup(node_mode: NodeMode, env: dict, prune: bool = False) -> None:
    turn_off(env, node_type=NodeType.SKALE, node_mode=node_mode)
    if prune:
        system_prune()
    if node_mode == NodeMode.PASSIVE:
        schain_name = env['SCHAIN_NAME']
        cleanup_no_lvm_datadir(chain_name=schain_name)
    else:
        cleanup_lvm_datadir()
    rm_dir(GLOBAL_SKALE_DIR)
    rm_dir(SKALE_DIR)
    cleanup_dir_content(NFTABLES_CHAIN_FOLDER_PATH)
    cleanup_docker_configuration()
