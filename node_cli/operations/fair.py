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

from skale.core.settings import BaseNodeSettings, FairBaseSettings, FairSettings, get_settings
from skale.core.types import EnvType

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
from node_cli.core.host import ensure_btrfs_kernel_module_autoloaded, prepare_host
from node_cli.core.nftables import configure_nftables
from node_cli.core.nginx import generate_nginx_config
from node_cli.core.schains import cleanup_no_lvm_datadir
from node_cli.core.static_config import get_fair_chain_name
from node_cli.core.node_options import mark_active_node, set_passive_node_options, upsert_node_mode
from node_cli.fair.record.chain_record import (
    get_fair_chain_record,
    migrate_chain_record,
    update_chain_record,
)
from node_cli.migrations.fair.from_boot import migrate_nftables_from_boot
from node_cli.operations.base import checked_host, turn_off
from node_cli.operations.common import configure_filebeat, unpack_backup_archive
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
from node_cli.utils.helper import cleanup_dir_content, rm_dir
from node_cli.utils.meta import FairCliMetaManager
from node_cli.utils.print_formatters import print_failed_requirements_checks
from node_cli.utils.node_type import NodeMode, NodeType
from node_cli.utils.settings import save_internal_settings

logger = logging.getLogger(__name__)


class FairUpdateType(Enum):
    REGULAR = 'regular'
    INFRA_ONLY = 'infra_only'
    FROM_BOOT = 'from_boot'


@checked_host
def init_fair_boot(
    settings: BaseNodeSettings,
    compose_env: dict,
    node_mode: NodeMode,
) -> None:
    sync_skale_node()
    cleanup_volume_artifacts(settings.block_device)

    ensure_btrfs_kernel_module_autoloaded()
    if not settings.skip_docker_config:
        configure_docker()

    configure_nftables(enable_monitoring=settings.monitoring_containers)

    prepare_host(env_type=settings.env_type)
    save_internal_settings(node_type=NodeType.FAIR, node_mode=NodeMode.ACTIVE)
    mark_active_node()

    configure_filebeat()
    generate_nginx_config()
    fair_settings = get_settings((FairSettings, FairBaseSettings))
    prepare_block_device(settings.block_device, force=fair_settings.enforce_btrfs)

    meta_manager = FairCliMetaManager()
    meta_manager.update_meta(
        VERSION,
        settings.node_version,
        distro.id(),
        distro.version(),
    )
    update_images(
        compose_env=compose_env,
        container_configs_dir=settings.container_configs_dir,
        node_type=NodeType.FAIR,
        node_mode=NodeMode.ACTIVE,
    )

    compose_up(
        env=compose_env,
        settings=settings,
        node_type=NodeType.FAIR,
        node_mode=NodeMode.ACTIVE,
        is_fair_boot=True,
    )


@checked_host
def init(
    settings: BaseNodeSettings,
    compose_env: dict,
    node_mode: NodeMode,
    indexer: bool,
    archive: bool,
    snapshot: str | None,
) -> bool:
    sync_skale_node()
    ensure_btrfs_kernel_module_autoloaded()
    cleanup_volume_artifacts(settings.block_device)

    if not settings.skip_docker_config:
        configure_docker()

    configure_nftables()
    configure_filebeat()
    generate_nginx_config()

    prepare_host(env_type=settings.env_type)
    save_internal_settings(node_type=NodeType.FAIR, node_mode=node_mode)

    fair_settings = get_settings((FairSettings, FairBaseSettings))
    prepare_block_device(settings.block_device, force=fair_settings.enforce_btrfs)

    update_images(
        compose_env=compose_env,
        container_configs_dir=settings.container_configs_dir,
        node_type=NodeType.FAIR,
        node_mode=node_mode,
    )
    compose_up(
        env=compose_env,
        settings=settings,
        node_type=NodeType.FAIR,
        node_mode=node_mode,
        services=list(REDIS_SERVICE_DICT),
    )

    upsert_node_mode(node_mode=node_mode)
    if node_mode == NodeMode.PASSIVE:
        logger.info('Setting passive node options')
        set_passive_node_options(archive=archive, indexer=indexer)
        if snapshot:
            logger.info('Waiting %s seconds for redis to start', REDIS_START_TIMEOUT)
            time.sleep(REDIS_START_TIMEOUT)
            trigger_skaled_snapshot_mode(env_type=settings.env_type, snapshot_from=snapshot)

    meta_manager = FairCliMetaManager()
    meta_manager.update_meta(
        VERSION,
        settings.node_version,
        distro.id(),
        distro.version(),
    )

    compose_up(env=compose_env, settings=settings, node_type=NodeType.FAIR, node_mode=node_mode)
    wait_for_container(BASE_PASSIVE_FAIR_COMPOSE_SERVICES['api'])
    time.sleep(REDIS_START_TIMEOUT)
    return True


@checked_host
def update_fair_boot(
    settings: BaseNodeSettings,
    compose_env: dict,
    node_mode: NodeMode = NodeMode.ACTIVE,
) -> bool:
    compose_rm(node_type=NodeType.FAIR, node_mode=node_mode, env=compose_env)
    remove_dynamic_containers()
    cleanup_volume_artifacts(settings.block_device)

    sync_skale_node()
    ensure_btrfs_kernel_module_autoloaded()

    if not settings.skip_docker_config:
        configure_docker()

    configure_nftables(enable_monitoring=settings.monitoring_containers)

    generate_nginx_config()
    fair_settings = get_settings((FairSettings, FairBaseSettings))
    prepare_block_device(settings.block_device, force=fair_settings.enforce_btrfs)

    prepare_host(settings.env_type)
    save_internal_settings(node_type=NodeType.FAIR, node_mode=NodeMode.ACTIVE)

    meta_manager = FairCliMetaManager()
    current_stream = meta_manager.get_meta_info().config_stream
    if not settings.skip_docker_cleanup and current_stream != settings.node_version:
        logger.info(
            'Stream version was changed from %s to %s',
            current_stream,
            settings.node_version,
        )
        docker_cleanup()

    meta_manager.update_meta(
        VERSION,
        settings.node_version,
        distro.id(),
        distro.version(),
    )
    update_images(
        compose_env=compose_env,
        container_configs_dir=settings.container_configs_dir,
        node_type=NodeType.FAIR,
        node_mode=NodeMode.ACTIVE,
    )
    compose_up(
        env=compose_env,
        settings=settings,
        node_type=NodeType.FAIR,
        node_mode=NodeMode.ACTIVE,
        is_fair_boot=True,
    )
    return True


@checked_host
def update(
    settings: BaseNodeSettings,
    compose_env: dict,
    node_mode: NodeMode,
    update_type: FairUpdateType,
    force_skaled_start: bool,
) -> bool:
    compose_rm(node_type=NodeType.FAIR, node_mode=node_mode, env=compose_env)
    if update_type not in (FairUpdateType.INFRA_ONLY, FairUpdateType.FROM_BOOT):
        remove_dynamic_containers()

    sync_skale_node()
    ensure_btrfs_kernel_module_autoloaded()

    if not settings.skip_docker_config:
        configure_docker()

    configure_nftables()
    generate_nginx_config()

    prepare_host(settings.env_type, allocation=True)
    save_internal_settings(node_type=NodeType.FAIR, node_mode=node_mode)
    meta_manager = FairCliMetaManager()
    current_stream = meta_manager.get_meta_info().config_stream
    if not settings.skip_docker_cleanup and current_stream != settings.node_version:
        logger.info(
            'Stream version was changed from %s to %s',
            current_stream,
            settings.node_version,
        )
        docker_cleanup()

    meta_manager.update_meta(
        VERSION,
        settings.node_version,
        distro.id(),
        distro.version(),
    )

    fair_chain_name = get_fair_chain_name(settings.env_type)
    if update_type == FairUpdateType.FROM_BOOT:
        migrate_nftables_from_boot(chain_name=fair_chain_name)

    update_images(
        compose_env=compose_env,
        container_configs_dir=settings.container_configs_dir,
        node_type=NodeType.FAIR,
        node_mode=node_mode,
    )

    compose_up(
        env=compose_env,
        settings=settings,
        node_type=NodeType.FAIR,
        node_mode=node_mode,
        services=list(REDIS_SERVICE_DICT),
    )
    wait_for_container(REDIS_SERVICE_DICT['redis'])
    time.sleep(REDIS_START_TIMEOUT)
    if update_type == FairUpdateType.FROM_BOOT:
        migrate_chain_record(settings.env_type, settings.node_version)
    update_chain_record(settings.env_type, force_skaled_start=force_skaled_start)
    compose_up(env=compose_env, settings=settings, node_type=NodeType.FAIR, node_mode=node_mode)
    return True


def restore(
    node_mode: NodeMode,
    settings: BaseNodeSettings,
    compose_env: dict,
    backup_path: str,
    config_only: bool = False,
) -> bool:
    unpack_backup_archive(backup_path)
    failed_checks = run_host_checks(
        settings.block_device,
        TYPE,
        node_mode,
        settings.env_type,
        CONTAINER_CONFIG_PATH,
        check_type=CheckType.PREINSTALL,
    )
    if failed_checks:
        print_failed_requirements_checks(failed_checks)
        return False

    ensure_btrfs_kernel_module_autoloaded()

    if not settings.skip_docker_config:
        configure_docker()

    configure_nftables(enable_monitoring=settings.monitoring_containers)

    meta_manager = FairCliMetaManager()
    meta_manager.update_meta(
        VERSION,
        settings.node_version,
        distro.id(),
        distro.version(),
    )

    if not config_only:
        compose_up(env=compose_env, settings=settings, node_type=NodeType.FAIR, node_mode=node_mode)

    failed_checks = run_host_checks(
        settings.block_device,
        TYPE,
        node_mode,
        settings.env_type,
        CONTAINER_CONFIG_PATH,
        check_type=CheckType.POSTINSTALL,
    )
    if failed_checks:
        print_failed_requirements_checks(failed_checks)
        return False
    return True


def cleanup(node_mode: NodeMode, compose_env: dict, prune: bool = False) -> None:
    turn_off(compose_env, node_type=NodeType.FAIR, node_mode=node_mode)
    if prune:
        system_prune()
    cleanup_no_lvm_datadir()
    rm_dir(GLOBAL_SKALE_DIR)
    rm_dir(SKALE_DIR)
    cleanup_dir_content(NFTABLES_CHAIN_FOLDER_PATH)
    cleanup_docker_configuration()


def trigger_skaled_snapshot_mode(env_type: EnvType, snapshot_from: str = 'any') -> None:
    record = get_fair_chain_record(env_type)
    if not snapshot_from:
        snapshot_from = 'any'
    logger.info('Triggering skaled snapshot mode, snapshot_from: %s', snapshot_from)
    record.set_snapshot_from(snapshot_from)


def repair(env_type: EnvType, snapshot_from: str = 'any') -> None:
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
    trigger_skaled_snapshot_mode(env_type=env_type, snapshot_from=snapshot_from)
    logger.info('Starting admin')
    start_container_by_name(container_name=container_name)
    logger.info('Fair node repair completed successfully')
