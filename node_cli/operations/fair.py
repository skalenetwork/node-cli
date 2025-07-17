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
from node_cli.fair.record.chain_record import migrate_chain_record
from node_cli.migrations.fair.from_boot import migrate_nftables_from_boot
from node_cli.operations.base import checked_host, turn_off
from node_cli.operations.common import configure_filebeat, configure_flask, unpack_backup_archive
from node_cli.operations.config_repo import (
    sync_skale_node,
    update_images,
)
from node_cli.operations.volume import cleanup_volume_artifacts, prepare_block_device
from node_cli.utils.docker_utils import (
    REDIS_SERVICE_DICT,
    REDIS_START_TIMEOUT,
    NodeType,
    compose_rm,
    compose_up,
    docker_cleanup,
    remove_dynamic_containers,
    wait_for_container,
)
from node_cli.utils.helper import cleanup_dir_content, rm_dir, str_to_bool
from node_cli.utils.meta import FairCliMetaManager
from node_cli.utils.print_formatters import print_failed_requirements_checks

logger = logging.getLogger(__name__)


class FairUpdateType(Enum):
    REGULAR = 'regular'
    INFRA_ONLY = 'infra_only'
    FROM_BOOT = 'from_boot'


@checked_host
def init(env_filepath: str, env: dict) -> bool:
    sync_skale_node()
    ensure_btrfs_kernel_module_autoloaded()
    cleanup_volume_artifacts(env['DISK_MOUNTPOINT'])

    if env.get('SKIP_DOCKER_CONFIG') != 'True':
        configure_docker()

    configure_nftables()
    configure_filebeat()
    configure_flask()
    generate_nginx_config()

    prepare_host(env_filepath, env_type=env['ENV_TYPE'])
    link_env_file()

    prepare_block_device(env['DISK_MOUNTPOINT'], force=env['ENFORCE_BTRFS'] == 'True')

    meta_manager = FairCliMetaManager()
    meta_manager.update_meta(
        VERSION,
        env['CONTAINER_CONFIGS_STREAM'],
        distro.id(),
        distro.version(),
    )
    update_images(env=env, node_type=NodeType.FAIR)
    compose_up(env=env, node_type=NodeType.FAIR)
    wait_for_container(REDIS_SERVICE_DICT['redis'])
    time.sleep(REDIS_START_TIMEOUT)
    return True


@checked_host
def update_fair_boot(env_filepath: str, env: dict) -> bool:
    compose_rm(node_type=NodeType.FAIR, env=env)
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

    meta_manager = FairCliMetaManager()
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
    update_images(env=env, node_type=NodeType.FAIR)
    compose_up(env=env, node_type=NodeType.FAIR, is_fair_boot=True)
    return True


@checked_host
def update_fair(env_filepath: str, env: dict, update_type: FairUpdateType) -> bool:
    compose_rm(node_type=NodeType.FAIR, env=env)
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

    if update_type == FairUpdateType.FROM_BOOT:
        migrate_nftables_from_boot()

    update_images(env=env, node_type=NodeType.FAIR)

    compose_up(env=env, node_type=NodeType.FAIR, services=list(REDIS_SERVICE_DICT))
    wait_for_container(REDIS_SERVICE_DICT['redis'])
    time.sleep(REDIS_START_TIMEOUT)
    if update_type == FairUpdateType.FROM_BOOT:
        migrate_chain_record(env)

    compose_up(env=env, node_type=NodeType.FAIR)
    return True


def restore_fair(env, backup_path, config_only=False):
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

    meta_manager = FairCliMetaManager()
    meta_manager.update_meta(
        VERSION,
        env['CONTAINER_CONFIGS_STREAM'],
        distro.id(),
        distro.version(),
    )

    if not config_only:
        compose_up(env=env, node_type=NodeType.FAIR)

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


def cleanup(env) -> None:
    turn_off(env, node_type=NodeType.FAIR)
    cleanup_no_lvm_datadir()
    rm_dir(GLOBAL_SKALE_DIR)
    rm_dir(SKALE_DIR)
    cleanup_dir_content(NFTABLES_CHAIN_FOLDER_PATH)
    cleanup_docker_configuration()
