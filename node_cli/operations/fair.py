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

import logging
import time
from enum import Enum

import distro

from node_cli.cli.info import TYPE, VERSION
from node_cli.configs import (
    CONTAINER_CONFIG_PATH,
    GLOBAL_SKALE_DIR,
    NFTABLES_CHAIN_FOLDER_PATH,
    SKALE_DIR,
)
from node_cli.core.checks import CheckType
from node_cli.core.checks import run_checks as run_host_checks
from node_cli.core.docker_config import cleanup_docker_configuration, configure_docker
from node_cli.core.host import ensure_btrfs_kernel_module_autoloaded, link_env_file, prepare_host
from node_cli.core.nftables import configure_nftables
from node_cli.core.nginx import generate_nginx_config
from node_cli.core.schains import cleanup_no_lvm_datadir
from node_cli.core.static_config import get_fair_chain_name
from node_cli.core.node_options import set_passive_node_options, upsert_node_mode
from node_cli.fair.record.chain_record import (
    get_fair_chain_record,
    migrate_chain_record,
    update_chain_record,
)
from node_cli.migrations.fair.from_boot import migrate_nftables_from_boot
from node_cli.operations.base import checked_host, turn_off
from node_cli.operations.common import configure_filebeat, configure_flask, unpack_backup_archive
from node_cli.operations.config_repo import (
    sync_skale_node,
    update_images,
)
from node_cli.operations.volume import cleanup_volume_artifacts, prepare_block_device
from node_cli.utils.docker_utils import (
    BASE_PASSIVE_FAIR_COMPOSE_SERVICES,
    REDIS_SERVICE_DICT,
    REDIS_START_TIMEOUT,
    compose_rm,
    compose_up,
    docker_cleanup,
    is_admin_running,
    remove_dynamic_containers,
    start_container_by_name,
    stop_container_by_name,
    system_prune,
    wait_for_container,
)
from node_cli.utils.helper import cleanup_dir_content, rm_dir, str_to_bool
from node_cli.utils.meta import FairCliMetaManager
from node_cli.utils.print_formatters import print_failed_requirements_checks
from node_cli.utils.node_type import NodeMode, NodeType

logger = logging.getLogger(__name__)


class FairUpdateType(Enum):
    REGULAR = 'regular'
    INFRA_ONLY = 'infra_only'
    FROM_BOOT = 'from_boot'


@checked_host
def init(
    env_filepath: str,
    env: dict,
    node_mode: NodeMode,
    indexer: bool,
    archive: bool,
    snapshot: str | None,
) -> bool:
    sync_skale_node()
    ensure_btrfs_kernel_module_autoloaded()
    cleanup_volume_artifacts(env['BLOCK_DEVICE'])

    if env.get('SKIP_DOCKER_CONFIG') != 'True':
        configure_docker()

    configure_nftables()
    configure_filebeat()
    configure_flask()
    generate_nginx_config()

    prepare_host(env_filepath, env_type=env['ENV_TYPE'])
    link_env_file()

    prepare_block_device(env['BLOCK_DEVICE'], force=env['ENFORCE_BTRFS'] == 'True')

    update_images(env=env, node_type=NodeType.FAIR, node_mode=node_mode)
    compose_up(
        env=env, node_type=NodeType.FAIR, node_mode=node_mode, services=list(REDIS_SERVICE_DICT)
    )

    upsert_node_mode(node_mode=node_mode)
    if node_mode == NodeMode.PASSIVE:
        logger.info('Setting passive node options')
        set_passive_node_options(archive=archive, indexer=indexer)
        if snapshot:
            logger.info('Waiting %s seconds for redis to start', REDIS_START_TIMEOUT)
            time.sleep(REDIS_START_TIMEOUT)
            trigger_skaled_snapshot_mode(env=env, snapshot_from=snapshot)

    meta_manager = FairCliMetaManager()
    meta_manager.update_meta(
        VERSION,
        env['NODE_VERSION'],
        distro.id(),
        distro.version(),
    )

    compose_up(env=env, node_type=NodeType.FAIR, node_mode=node_mode)
    wait_for_container(BASE_PASSIVE_FAIR_COMPOSE_SERVICES['api'])
    time.sleep(REDIS_START_TIMEOUT)
    return True


@checked_host
def update_fair_boot(env_filepath: str, env: dict, node_mode: NodeMode = NodeMode.ACTIVE) -> bool:
    compose_rm(node_type=NodeType.FAIR, node_mode=node_mode, env=env)
    remove_dynamic_containers()
    cleanup_volume_artifacts(env['BLOCK_DEVICE'])

    sync_skale_node()
    ensure_btrfs_kernel_module_autoloaded()

    if env.get('SKIP_DOCKER_CONFIG') != 'True':
        configure_docker()

    enable_monitoring = str_to_bool(env.get('MONITORING_CONTAINERS', 'False'))
    configure_nftables(enable_monitoring=enable_monitoring)

    generate_nginx_config()
    prepare_block_device(env['BLOCK_DEVICE'], force=env['ENFORCE_BTRFS'] == 'True')

    prepare_host(env_filepath, env['ENV_TYPE'])

    meta_manager = FairCliMetaManager()
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
        distro.id(),
        distro.version(),
    )
    update_images(env=env, node_type=NodeType.FAIR, node_mode=NodeMode.ACTIVE)
    compose_up(env=env, node_type=NodeType.FAIR, node_mode=NodeMode.ACTIVE, is_fair_boot=True)
    return True


@checked_host
def update(
    env_filepath: str,
    env: dict,
    node_mode: NodeMode,
    update_type: FairUpdateType,
    force_skaled_start: bool,
) -> bool:
    compose_rm(node_type=NodeType.FAIR, node_mode=node_mode, env=env)
    if update_type not in (FairUpdateType.INFRA_ONLY, FairUpdateType.FROM_BOOT):
        remove_dynamic_containers()

    sync_skale_node()
    ensure_btrfs_kernel_module_autoloaded()

    if env.get('SKIP_DOCKER_CONFIG') != 'True':
        configure_docker()

    configure_nftables()
    generate_nginx_config()

    prepare_host(env_filepath, env['ENV_TYPE'], allocation=True)
    meta_manager = FairCliMetaManager()
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
        distro.id(),
        distro.version(),
    )

    fair_chain_name = get_fair_chain_name(env)
    if update_type == FairUpdateType.FROM_BOOT:
        migrate_nftables_from_boot(chain_name=fair_chain_name)

    update_images(env=env, node_type=NodeType.FAIR, node_mode=node_mode)

    compose_up(
        env=env, node_type=NodeType.FAIR, node_mode=node_mode, services=list(REDIS_SERVICE_DICT)
    )
    wait_for_container(REDIS_SERVICE_DICT['redis'])
    time.sleep(REDIS_START_TIMEOUT)
    if update_type == FairUpdateType.FROM_BOOT:
        migrate_chain_record(env)
    update_chain_record(env, force_skaled_start=force_skaled_start)
    compose_up(env=env, node_type=NodeType.FAIR, node_mode=node_mode)
    return True


def restore(node_mode: NodeMode, env, backup_path, config_only=False):
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

    meta_manager = FairCliMetaManager()
    meta_manager.update_meta(
        VERSION,
        env['NODE_VERSION'],
        distro.id(),
        distro.version(),
    )

    if not config_only:
        compose_up(env=env, node_type=NodeType.FAIR, node_mode=node_mode)

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


def cleanup(node_mode: NodeMode, env: dict, prune: bool = False) -> None:
    turn_off(env, node_type=NodeType.FAIR, node_mode=node_mode)
    if prune:
        system_prune()
    cleanup_no_lvm_datadir()
    rm_dir(GLOBAL_SKALE_DIR)
    rm_dir(SKALE_DIR)
    cleanup_dir_content(NFTABLES_CHAIN_FOLDER_PATH)
    cleanup_docker_configuration()


def trigger_skaled_snapshot_mode(env: dict, snapshot_from: str = 'any') -> None:
    record = get_fair_chain_record(env)
    if not snapshot_from:
        snapshot_from = 'any'
    logger.info('Triggering skaled snapshot mode, snapshot_from: %s', snapshot_from)
    record.set_snapshot_from(snapshot_from)


def repair(env: dict, snapshot_from: str = 'any') -> None:
    logger.info('Starting fair node repair')
    container_name = 'sk_admin'
    if is_admin_running():
        logger.info('Stopping admin container')
        stop_container_by_name(container_name=container_name)
    logger.info('Removing chain container')
    remove_dynamic_containers()
    logger.info('Cleaning up datadir')
    cleanup_no_lvm_datadir()
    logger.info('Requesting fair node repair')
    trigger_skaled_snapshot_mode(env=env, snapshot_from=snapshot_from)
    logger.info('Starting admin')
    start_container_by_name(container_name=container_name)
    logger.info('Fair node repair completed successfully')
