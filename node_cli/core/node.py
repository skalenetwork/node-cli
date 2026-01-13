#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
#
#   Copyright (C) 2019 SKALE Labs
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

import datetime
import logging
import os
import tarfile
import time
from contextlib import contextmanager
from enum import Enum
from pathlib import Path
from typing import Optional, Tuple

import docker

from node_cli.cli import __version__
from node_cli.configs import (
    BACKUP_ARCHIVE_NAME,
    CONTAINER_CONFIG_PATH,
    FILESTORAGE_MAPPING,
    INIT_ENV_FILEPATH,
    LOG_PATH,
    RESTORE_SLEEP_TIMEOUT,
    SCHAINS_MNT_DIR_REGULAR,
    SCHAINS_MNT_DIR_SINGLE_CHAIN,
    SKALE_DIR,
    SKALE_STATE_DIR,
    TM_INIT_TIMEOUT,
)
from node_cli.configs.cli_logger import LOG_DATA_PATH as CLI_LOG_DATA_PATH
from node_cli.configs.user import SKALE_DIR_ENV_FILEPATH, get_validated_user_config
from node_cli.core.checks import run_checks as run_host_checks
from node_cli.core.host import get_flask_secret_key, is_node_inited, save_env_params
from node_cli.core.resources import update_resource_allocation
from node_cli.core.node_options import (
    active_fair,
    active_skale,
    upsert_node_mode,
    passive_skale,
    passive_fair,
)
from node_cli.migrations.focal_to_jammy import migrate as migrate_2_6
from node_cli.operations import (
    cleanup_skale_op,
    configure_nftables,
    init_op,
    init_passive_op,
    restore_op,
    turn_off_op,
    turn_on_op,
    update_op,
    update_passive_op,
)
from node_cli.utils.decorators import check_inited, check_not_inited, check_user
from node_cli.utils.docker_utils import (
    BASE_FAIR_BOOT_COMPOSE_SERVICES,
    BASE_FAIR_COMPOSE_SERVICES,
    BASE_SKALE_COMPOSE_SERVICES,
    BASE_PASSIVE_COMPOSE_SERVICES,
    BASE_PASSIVE_FAIR_COMPOSE_SERVICES,
    is_admin_running,
    is_api_running,
)
from node_cli.utils.exit_codes import CLIExitCodes
from node_cli.utils.helper import (
    error_exit,
    get_request,
    post_request,
)
from node_cli.utils.meta import CliMetaManager
from node_cli.utils.node_type import NodeType, NodeMode
from node_cli.utils.print_formatters import (
    print_failed_requirements_checks,
    print_node_cmd_error,
    print_node_info,
)
from node_cli.utils.texts import safe_load_texts

logger = logging.getLogger(__name__)
TEXTS = safe_load_texts()

BLUEPRINT_NAME = 'node'


class NodeStatuses(Enum):
    """This class contains possible node statuses."""

    ACTIVE = 0
    LEAVING = 1
    FROZEN = 2
    IN_MAINTENANCE = 3
    LEFT = 4
    NOT_CREATED = 5


def is_update_safe(node_mode: NodeMode) -> bool:
    if not is_admin_running():
        if node_mode == NodeMode.PASSIVE:
            return True
        elif not is_api_running():
            return True
    status, payload = get_request(BLUEPRINT_NAME, 'update-safe')
    if status == 'error':
        return False
    if not isinstance(payload, dict):
        return False
    safe = bool(payload.get('update_safe'))
    if not safe:
        logger.info('Locked schains: %s', payload.get('unsafe_chains'))
    return safe


@check_inited
@check_user
def register_node(name, p2p_ip, public_ip, port, domain_name):
    if not is_node_inited():
        print(TEXTS['node']['not_inited'])
        return

    # todo: add name, ips and port checks
    json_data = {
        'name': name,
        'ip': p2p_ip,
        'publicIP': public_ip,
        'port': port,
        'domain_name': domain_name,
    }
    status, payload = post_request(blueprint=BLUEPRINT_NAME, method='register', json=json_data)
    if status == 'ok':
        msg = TEXTS['node']['registered']
        logger.info(msg)
        print(msg)
    else:
        error_msg = payload
        logger.error(f'Registration error {error_msg}')
        error_exit(error_msg, exit_code=CLIExitCodes.BAD_API_RESPONSE)


@check_not_inited
def init(env_filepath: str, node_type: NodeType) -> None:
    node_mode = NodeMode.ACTIVE
    env = compose_node_env(env_filepath=env_filepath, node_type=node_type, node_mode=node_mode)

    init_op(env_filepath=env_filepath, env=env, node_mode=node_mode)
    logger.info('Waiting for containers initialization')
    time.sleep(TM_INIT_TIMEOUT)
    if not is_base_containers_alive(node_type=node_type, node_mode=node_mode):
        error_exit('Containers are not running', exit_code=CLIExitCodes.OPERATION_EXECUTION_ERROR)
    logger.info('Generating resource allocation file ...')
    update_resource_allocation(env['ENV_TYPE'])
    logger.info('Init procedure finished')


@check_not_inited
def restore(backup_path, env_filepath, node_type: NodeType, no_snapshot=False, config_only=False):
    node_mode = NodeMode.ACTIVE
    env = compose_node_env(env_filepath=env_filepath, node_type=node_type, node_mode=node_mode)
    if env is None:
        return
    save_env_params(env_filepath)
    env['SKALE_DIR'] = SKALE_DIR

    if not no_snapshot:
        logger.info('Adding BACKUP_RUN to env ...')
        env['BACKUP_RUN'] = 'True'  # should be str

    restored_ok = restore_op(env, backup_path, node_type=node_type, config_only=config_only)
    if not restored_ok:
        error_exit('Restore operation failed', exit_code=CLIExitCodes.OPERATION_EXECUTION_ERROR)
    time.sleep(RESTORE_SLEEP_TIMEOUT)
    logger.info('Generating resource allocation file ...')
    update_resource_allocation(env['ENV_TYPE'])
    print('Node is restored from backup')


@check_not_inited
def init_passive(
    env_filepath: str, indexer: bool, archive: bool, snapshot: bool, snapshot_from: Optional[str]
) -> None:
    node_mode = NodeMode.PASSIVE
    env = compose_node_env(env_filepath, node_type=NodeType.SKALE, node_mode=node_mode)
    if env is None:
        return
    init_passive_op(env_filepath, env, indexer, archive, snapshot, snapshot_from)
    logger.info('Waiting for containers initialization')
    time.sleep(TM_INIT_TIMEOUT)
    if not is_base_containers_alive(node_type=NodeType.SKALE, node_mode=node_mode):
        error_exit('Containers are not running', exit_code=CLIExitCodes.OPERATION_EXECUTION_ERROR)
    logger.info('Passive node initialized successfully')


@check_inited
@check_user
def update_passive(env_filepath: str, unsafe_ok: bool = False) -> None:
    logger.info('Node update started')
    prev_version = CliMetaManager().get_meta_info().version
    if (__version__ == 'test' or __version__.startswith('2.6')) and prev_version == '2.5.0':
        migrate_2_6()
    env = compose_node_env(env_filepath, node_type=NodeType.SKALE, node_mode=NodeMode.PASSIVE)
    update_ok = update_passive_op(env_filepath, env)
    if update_ok:
        logger.info('Waiting for containers initialization')
        time.sleep(TM_INIT_TIMEOUT)
    alive = is_base_containers_alive(node_type=NodeType.SKALE, node_mode=NodeMode.PASSIVE)
    if not update_ok or not alive:
        print_node_cmd_error()
        return
    else:
        logger.info('Node update finished')


@check_user
def cleanup(node_mode: NodeMode, prune: bool = False) -> None:
    node_mode = upsert_node_mode(node_mode=node_mode)
    env = compose_node_env(
        SKALE_DIR_ENV_FILEPATH,
        save=False,
        node_type=NodeType.SKALE,
        node_mode=node_mode,
        skip_user_conf_validation=True,
    )
    cleanup_skale_op(node_mode=node_mode, env=env, prune=prune)
    logger.info('SKALE node was cleaned up, all containers and data removed')


def compose_node_env(
    env_filepath: str,
    node_type: NodeType,
    node_mode: NodeMode,
    inited_node: bool = False,
    sync_schains: Optional[bool] = None,
    pull_config_for_schain: Optional[str] = None,
    save: bool = True,
    is_fair_boot: bool = False,
    skip_user_conf_validation: bool = False,
) -> dict[str, str]:
    if env_filepath is not None:
        user_config = get_validated_user_config(
            node_type=node_type,
            node_mode=node_mode,
            env_filepath=env_filepath,
            is_fair_boot=is_fair_boot,
            skip_user_conf_validation=skip_user_conf_validation,
        )
        if save:
            save_env_params(env_filepath)
    else:
        user_config = get_validated_user_config(
            node_type=node_type,
            env_filepath=INIT_ENV_FILEPATH,
            is_fair_boot=is_fair_boot,
            skip_user_conf_validation=skip_user_conf_validation,
        )

    if node_mode == NodeMode.PASSIVE or node_type == NodeType.FAIR:
        mnt_dir = SCHAINS_MNT_DIR_SINGLE_CHAIN
    else:
        mnt_dir = SCHAINS_MNT_DIR_REGULAR

    env = {
        'SKALE_DIR': SKALE_DIR,
        'SCHAINS_MNT_DIR': mnt_dir,
        'FILESTORAGE_MAPPING': FILESTORAGE_MAPPING,
        'SKALE_LIB_PATH': SKALE_STATE_DIR,
        **user_config.to_env(),
    }

    if inited_node and not node_mode == NodeMode.PASSIVE:
        env['FLASK_SECRET_KEY'] = get_flask_secret_key()

    if sync_schains and not node_mode == NodeMode.PASSIVE:
        env['BACKUP_RUN'] = 'True'

    if pull_config_for_schain:
        env['PULL_CONFIG_FOR_SCHAIN'] = pull_config_for_schain

    return {k: v for k, v in env.items() if v != ''}


@check_inited
@check_user
def update(
    env_filepath: str,
    pull_config_for_schain: Optional[str],
    node_type: NodeType,
    node_mode: NodeMode,
    unsafe_ok: bool = False,
) -> None:
    node_mode = upsert_node_mode(node_mode=node_mode)

    if not unsafe_ok and not is_update_safe(node_mode=node_mode):
        error_msg = 'Cannot update safely'
        error_exit(error_msg, exit_code=CLIExitCodes.UNSAFE_UPDATE)

    prev_version = CliMetaManager().get_meta_info().version
    if (__version__ == 'test' or __version__.startswith('2.6')) and prev_version == '2.5.0':
        migrate_2_6()
    logger.info('Node update started')
    env = compose_node_env(
        env_filepath,
        inited_node=True,
        sync_schains=False,
        pull_config_for_schain=pull_config_for_schain,
        node_type=node_type,
        node_mode=node_mode,
    )
    update_ok = update_op(env_filepath, env, node_mode=node_mode)
    if update_ok:
        logger.info('Waiting for containers initialization')
        time.sleep(TM_INIT_TIMEOUT)
    alive = is_base_containers_alive(node_type=node_type, node_mode=node_mode)
    if not update_ok or not alive:
        print_node_cmd_error()
        return
    else:
        logger.info('Node update finished')


def get_node_signature(validator_id):
    params = {'validator_id': validator_id}
    status, payload = get_request(blueprint=BLUEPRINT_NAME, method='signature', params=params)
    if status == 'ok':
        return payload['signature']
    else:
        return payload


def backup(path):
    backup_filepath = get_backup_filepath(path)
    create_backup_archive(backup_filepath)


def get_backup_filename():
    time = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d-%H-%M-%S')
    return f'{BACKUP_ARCHIVE_NAME}-{time}.tar.gz'


def get_backup_filepath(base_path):
    return os.path.abspath(os.path.join(base_path, get_backup_filename()))


@contextmanager
def chdir(dest):
    old = os.getcwd()
    try:
        os.chdir(dest)
        yield
    finally:
        os.chdir(old)


def pack_dir(source: str, dest: str, exclude: Tuple[str] = ()):
    logger.info('Packing dir %s to %s excluding %s', source, dest, exclude)

    source, dest = Path(source), Path(dest)
    exclude = [Path(e).relative_to(source.parent) for e in exclude]

    def logfilter(tarinfo):
        path = Path(tarinfo.name)
        for e in exclude:
            logger.debug('Checking if %s is parent of %s', e, tarinfo.name)
            try:
                path.relative_to(e)
            except ValueError:
                pass
            else:
                logger.debug('Excluding %s', tarinfo.name)
                return None
        return tarinfo

    with chdir(source.parent):
        with tarfile.open(dest, 'w:gz') as tar:
            tar.add(source.name, filter=logfilter)
    logger.info('Packing finished %s', source)


def create_backup_archive(backup_filepath):
    print('Creating backup archive...')
    cli_log_path = CLI_LOG_DATA_PATH
    container_log_path = LOG_PATH
    pack_dir(SKALE_DIR, backup_filepath, exclude=(cli_log_path, container_log_path))
    print(f'Backup archive successfully created {backup_filepath}')


def set_maintenance_mode_on():
    print('Setting maintenance mode on...')
    status, payload = post_request(blueprint=BLUEPRINT_NAME, method='maintenance-on')
    if status == 'ok':
        msg = TEXTS['node']['maintenance_on']
        logger.info(msg)
        print(msg)
    else:
        error_msg = payload
        logger.error(f'Set maintenance mode error {error_msg}')
        error_exit(error_msg, exit_code=CLIExitCodes.BAD_API_RESPONSE)


def set_maintenance_mode_off():
    print('Setting maintenance mode off...')
    status, payload = post_request(blueprint=BLUEPRINT_NAME, method='maintenance-off')
    if status == 'ok':
        msg = TEXTS['node']['maintenance_off']
        logger.info(msg)
        print(msg)
    else:
        error_msg = payload
        logger.error(f'Remove from maintenance mode error {error_msg}')
        error_exit(error_msg, exit_code=CLIExitCodes.BAD_API_RESPONSE)


@check_inited
@check_user
def turn_off(node_type: NodeType, maintenance_on: bool = False, unsafe_ok: bool = False) -> None:
    node_mode = upsert_node_mode()
    if not unsafe_ok and not is_update_safe(node_mode=node_mode):
        error_msg = 'Cannot turn off safely'
        error_exit(error_msg, exit_code=CLIExitCodes.UNSAFE_UPDATE)
    if maintenance_on:
        set_maintenance_mode_on()
    env = compose_node_env(
        SKALE_DIR_ENV_FILEPATH, save=False, node_type=node_type, node_mode=node_mode
    )
    turn_off_op(node_type=node_type, node_mode=node_mode, env=env)


@check_inited
@check_user
def turn_on(maintenance_off, sync_schains, env_file, node_type: NodeType) -> None:
    node_mode = upsert_node_mode()
    env = compose_node_env(
        env_file,
        inited_node=True,
        sync_schains=sync_schains,
        node_type=node_type,
        node_mode=node_mode,
    )
    turn_on_op(env=env, node_type=node_type, node_mode=node_mode)
    logger.info('Waiting for containers initialization')
    time.sleep(TM_INIT_TIMEOUT)
    if not is_base_containers_alive(node_type=node_type, node_mode=node_mode):
        print_node_cmd_error()
        return
    logger.info('Node turned on')
    if maintenance_off:
        set_maintenance_mode_off()


def get_expected_container_names(
    node_type: NodeType,
    node_mode: NodeMode,
    is_fair_boot: bool,
) -> list[str]:
    if node_type == NodeType.FAIR and is_fair_boot:
        services = BASE_FAIR_BOOT_COMPOSE_SERVICES
    elif active_fair(node_type, node_mode):
        services = BASE_FAIR_COMPOSE_SERVICES
    elif passive_fair(node_type, node_mode):
        services = BASE_PASSIVE_FAIR_COMPOSE_SERVICES
    elif active_skale(node_type, node_mode):
        services = BASE_SKALE_COMPOSE_SERVICES
    elif passive_skale(node_type, node_mode):
        services = BASE_PASSIVE_COMPOSE_SERVICES
    return list(services.values())


def is_base_containers_alive(
    node_type: NodeType,
    node_mode: NodeMode,
    is_fair_boot: bool = False,
) -> bool:
    base_container_names = get_expected_container_names(node_type, node_mode, is_fair_boot)

    dclient = docker.from_env()
    running_container_names = set(container.name for container in dclient.containers.list())

    for base_container in base_container_names:
        if base_container not in running_container_names:
            return False

    return True


def get_node_info_plain():
    status, payload = get_request(blueprint=BLUEPRINT_NAME, method='info')
    if status == 'ok':
        return payload['node_info']
    else:
        error_exit(payload, exit_code=CLIExitCodes.BAD_API_RESPONSE)


def get_node_info(format):
    node_info = get_node_info_plain()
    if format == 'json':
        print(node_info)
    elif node_info['status'] == NodeStatuses.NOT_CREATED.value:
        print(TEXTS['service']['node_not_registered'])
    else:
        print_node_info(node_info, get_node_status(int(node_info['status'])))


def get_node_status(status):
    node_status = NodeStatuses(status).name
    return TEXTS['node']['status'][node_status]


@check_inited
def set_domain_name(domain_name):
    print(f'Setting new domain name: {domain_name}')
    status, payload = post_request(
        blueprint=BLUEPRINT_NAME, method='set-domain-name', json={'domain_name': domain_name}
    )
    if status == 'ok':
        msg = TEXTS['node']['domain_name_changed']
        logger.info(msg)
        print(msg)
    else:
        error_exit(payload, exit_code=CLIExitCodes.BAD_API_RESPONSE)


def run_checks(
    node_type: NodeType,
    node_mode: NodeMode,
    network: str = 'mainnet',
    container_config_path: str = CONTAINER_CONFIG_PATH,
    disk: Optional[str] = None,
) -> None:
    if not is_node_inited():
        print(TEXTS['node']['not_inited'])
        return

    if disk is None:
        env_config = get_validated_user_config(node_type=node_type, node_mode=node_mode)
        disk = env_config.block_device
    failed_checks = run_host_checks(disk, node_type, node_mode, network, container_config_path)
    if not failed_checks:
        print('Requirements checking successfully finished!')
    else:
        print('Node does not fully meet the requirements!')
        print_failed_requirements_checks(failed_checks)


def configure_firewall_rules(enable_monitoring: bool = False) -> None:
    configure_nftables(enable_monitoring=enable_monitoring)
