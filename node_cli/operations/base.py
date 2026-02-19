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
from typing import Optional

import distro

from skale_core.settings import BaseNodeSettings, SkalePassiveSettings, SkaleSettings, get_settings

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
from node_cli.operations.common import configure_filebeat, unpack_backup_archive
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
from node_cli.utils.helper import cleanup_dir_content, rm_dir
from node_cli.utils.meta import CliMetaManager, FairCliMetaManager
from node_cli.utils.node_type import NodeMode, NodeType
from node_cli.utils.print_formatters import print_failed_requirements_checks
from node_cli.utils.settings import save_internal_settings

logger = logging.getLogger(__name__)


def checked_host(func):
    @functools.wraps(func)
    def wrapper(
        settings: BaseNodeSettings, compose_env: dict, node_mode: NodeMode, *args, **kwargs
    ):
        download_skale_node(settings.node_version, settings.container_configs_dir or None)
        failed_checks = run_host_checks(
            settings.block_device,
            TYPE,
            node_mode,
            settings.env_type,
            CONTAINER_CONFIG_TMP_PATH,
            check_type=CheckType.PREINSTALL,
        )
        if failed_checks:
            print_failed_requirements_checks(failed_checks)
            return False

        result = func(settings, compose_env, node_mode, *args, **kwargs)
        if not result:
            return result

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

    return wrapper


@checked_host
def update(settings: BaseNodeSettings, compose_env: dict, node_mode: NodeMode) -> bool:
    compose_rm(node_type=NodeType.SKALE, node_mode=node_mode, env=compose_env)
    remove_dynamic_containers()

    sync_skale_node()
    ensure_btrfs_kernel_module_autoloaded()

    if not settings.skip_docker_config:
        configure_docker()

    configure_nftables(enable_monitoring=settings.monitoring_containers)

    lvmpy_install(settings.block_device)
    generate_nginx_config()

    prepare_host(settings.env_type, allocation=True)
    save_internal_settings(node_type=NodeType.SKALE, node_mode=node_mode)
    init_shared_space_volume(settings.env_type)

    meta_manager = CliMetaManager()
    current_stream = meta_manager.get_meta_info().config_stream
    if not settings.skip_docker_cleanup and current_stream != settings.node_version:
        logger.info(
            'Stream version was changed from %s to %s',
            current_stream,
            settings.node_version,
        )
        docker_cleanup()

    skale_settings = get_settings(SkaleSettings)
    meta_manager.update_meta(
        VERSION,
        settings.node_version,
        skale_settings.docker_lvmpy_version,
        distro.id(),
        distro.version(),
    )
    update_images(
        compose_env=compose_env,
        container_configs_dir=settings.container_configs_dir,
        node_type=NodeType.SKALE,
        node_mode=node_mode,
    )
    compose_up(env=compose_env, settings=settings, node_type=NodeType.SKALE, node_mode=node_mode)
    return True


@checked_host
def init(settings: BaseNodeSettings, compose_env: dict, node_mode: NodeMode) -> None:
    sync_skale_node()
    ensure_btrfs_kernel_module_autoloaded()
    if not settings.skip_docker_config:
        configure_docker()

    configure_nftables(enable_monitoring=settings.monitoring_containers)

    prepare_host(env_type=settings.env_type)

    mark_active_node()

    configure_filebeat()
    generate_nginx_config()

    lvmpy_install(settings.block_device)
    init_shared_space_volume(settings.env_type)

    skale_settings = get_settings(SkaleSettings)
    meta_manager = CliMetaManager()
    meta_manager.update_meta(
        VERSION,
        settings.node_version,
        skale_settings.docker_lvmpy_version,
        distro.id(),
        distro.version(),
    )
    update_resource_allocation(env_type=settings.env_type)
    update_images(
        compose_env=compose_env,
        container_configs_dir=settings.container_configs_dir,
        node_type=NodeType.SKALE,
        node_mode=node_mode,
    )
    compose_up(env=compose_env, settings=settings, node_type=NodeType.SKALE, node_mode=node_mode)


def init_passive(
    settings: BaseNodeSettings,
    compose_env: dict,
    indexer: bool,
    archive: bool,
    snapshot: bool,
    snapshot_from: Optional[str],
) -> None:
    cleanup_volume_artifacts(settings.block_device)
    download_skale_node(settings.node_version, settings.container_configs_dir or None)
    sync_skale_node()

    if not settings.skip_docker_config:
        configure_docker()

    configure_nftables(enable_monitoring=settings.monitoring_containers)

    prepare_host(env_type=settings.env_type)
    save_internal_settings(node_type=NodeType.SKALE, node_mode=NodeMode.PASSIVE)
    failed_checks = run_host_checks(
        settings.block_device,
        TYPE,
        NodeMode.PASSIVE,
        settings.env_type,
        CONTAINER_CONFIG_PATH,
        check_type=CheckType.PREINSTALL,
    )
    if failed_checks:
        print_failed_requirements_checks(failed_checks)

    set_passive_node_options(archive=archive, indexer=indexer)

    ensure_filestorage_mapping()

    generate_nginx_config()
    passive_settings = get_settings(SkalePassiveSettings)
    prepare_block_device(settings.block_device, force=passive_settings.enforce_btrfs)

    meta_manager = CliMetaManager()
    meta_manager.update_meta(
        VERSION,
        settings.node_version,
        None,
        distro.id(),
        distro.version(),
    )
    update_resource_allocation(env_type=settings.env_type)

    if passive_settings.schain_name and (snapshot or snapshot_from):
        ts = int(time.time())
        update_node_cli_schain_status(
            passive_settings.schain_name, repair_ts=ts, snapshot_from=snapshot_from
        )

    update_images(
        compose_env=compose_env,
        container_configs_dir=settings.container_configs_dir,
        node_type=NodeType.SKALE,
        node_mode=NodeMode.PASSIVE,
    )
    compose_up(
        env=compose_env, settings=settings, node_type=NodeType.SKALE, node_mode=NodeMode.PASSIVE
    )


def update_passive(settings: BaseNodeSettings, compose_env: dict) -> bool:
    compose_rm(env=compose_env, node_type=NodeType.SKALE, node_mode=NodeMode.PASSIVE)
    remove_dynamic_containers()
    cleanup_volume_artifacts(settings.block_device)
    download_skale_node(settings.node_version, settings.container_configs_dir or None)
    sync_skale_node()

    if not settings.skip_docker_config:
        configure_docker()

    configure_nftables(enable_monitoring=settings.monitoring_containers)

    ensure_filestorage_mapping()

    passive_settings = get_settings(SkalePassiveSettings)
    prepare_block_device(settings.block_device, force=passive_settings.enforce_btrfs)
    generate_nginx_config()

    prepare_host(settings.env_type, allocation=True)
    save_internal_settings(node_type=NodeType.SKALE, node_mode=NodeMode.PASSIVE)

    failed_checks = run_host_checks(
        settings.block_device,
        TYPE,
        NodeMode.PASSIVE,
        settings.env_type,
        CONTAINER_CONFIG_PATH,
        check_type=CheckType.PREINSTALL,
    )
    if failed_checks:
        print_failed_requirements_checks(failed_checks)

    meta_manager = CliMetaManager()
    meta_manager.update_meta(
        VERSION,
        settings.node_version,
        None,
        distro.id(),
        distro.version(),
    )
    update_images(
        compose_env=compose_env,
        container_configs_dir=settings.container_configs_dir,
        node_type=NodeType.SKALE,
        node_mode=NodeMode.PASSIVE,
    )
    compose_up(
        env=compose_env, settings=settings, node_type=NodeType.SKALE, node_mode=NodeMode.PASSIVE
    )
    return True


def turn_off(compose_env: dict, node_type: NodeType, node_mode: NodeMode) -> None:
    logger.info('Turning off the node...')
    compose_rm(env=compose_env, node_type=node_type, node_mode=node_mode)
    remove_dynamic_containers()
    logger.info('Node was successfully turned off')


def turn_on(
    settings: BaseNodeSettings,
    compose_env: dict,
    node_type: NodeType,
    node_mode: NodeMode,
    backup_run: bool = False,
) -> None:
    logger.info('Turning on the node...')
    if node_type == NodeType.FAIR:
        meta_manager = FairCliMetaManager()
        meta_manager.update_meta(
            VERSION,
            settings.node_version,
            distro.id(),
            distro.version(),
        )
    else:
        skale_settings = get_settings((SkaleSettings, SkalePassiveSettings))
        docker_lvmpy_version = (
            skale_settings.docker_lvmpy_version
            if isinstance(skale_settings, SkaleSettings)
            else None
        )
        meta_manager = CliMetaManager()
        meta_manager.update_meta(
            VERSION, settings.node_version, docker_lvmpy_version, distro.id(), distro.version()
        )
    if not settings.skip_docker_config:
        configure_docker()

    configure_nftables(enable_monitoring=settings.monitoring_containers)

    save_internal_settings(node_type=node_type, node_mode=node_mode, backup_run=backup_run)
    logger.info('Launching containers on the node...')
    compose_up(env=compose_env, settings=settings, node_type=node_type, node_mode=node_mode)


def restore(
    settings: BaseNodeSettings,
    compose_env: dict,
    backup_path: str,
    node_type: NodeType,
    config_only: bool = False,
    backup_run: bool = False,
) -> bool:
    node_mode = upsert_node_mode(node_mode=NodeMode.ACTIVE)
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

    lvmpy_install(settings.block_device)
    init_shared_space_volume(settings.env_type)

    skale_settings = get_settings(SkaleSettings)
    meta_manager = CliMetaManager()
    meta_manager.update_meta(
        VERSION,
        settings.node_version,
        skale_settings.docker_lvmpy_version,
        distro.id(),
        distro.version(),
    )
    save_internal_settings(node_type=node_type, node_mode=node_mode, backup_run=backup_run)
    if not config_only:
        compose_up(env=compose_env, settings=settings, node_type=node_type, node_mode=node_mode)

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


def cleanup_passive(compose_env: dict, schain_name: str) -> None:
    turn_off(compose_env, node_type=NodeType.SKALE, node_mode=NodeMode.PASSIVE)
    cleanup_no_lvm_datadir(chain_name=schain_name)
    rm_dir(GLOBAL_SKALE_DIR)
    rm_dir(SKALE_DIR)


def cleanup(
    node_mode: NodeMode, compose_env: dict, schain_name: Optional[str] = None, prune: bool = False
) -> None:
    turn_off(compose_env, node_type=NodeType.SKALE, node_mode=node_mode)
    if prune:
        system_prune()
    if node_mode == NodeMode.PASSIVE:
        cleanup_no_lvm_datadir(chain_name=schain_name)
    else:
        cleanup_lvm_datadir()
    rm_dir(GLOBAL_SKALE_DIR)
    rm_dir(SKALE_DIR)
    cleanup_dir_content(NFTABLES_CHAIN_FOLDER_PATH)
    cleanup_docker_configuration()
