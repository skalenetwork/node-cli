#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
#
#   Copyright (C) 2019 SKALE Labs
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

from node_cli.configs import (
    BACKUP_ARCHIVE_NAME,
    CONTAINER_CONFIG_PATH,
    FILESTORAGE_MAPPING,
    INIT_ENV_FILEPATH,
    LOG_PATH,
    RESTORE_SLEEP_TIMEOUT,
    SCHAINS_MNT_DIR_REGULAR,
    SCHAINS_MNT_DIR_SYNC,
    SKALE_DIR,
    SKALE_STATE_DIR,
    TM_INIT_TIMEOUT
)
from node_cli.configs.env import get_env_config
from node_cli.configs.cli_logger import LOG_DATA_PATH as CLI_LOG_DATA_PATH

from node_cli.core.iptables import configure_iptables
from node_cli.core.host import (
    is_node_inited, save_env_params, get_flask_secret_key
)
from node_cli.core.checks import run_checks as run_host_checks
from node_cli.core.resources import update_resource_allocation
from node_cli.operations import (
    update_op,
    init_op,
    turn_off_op,
    turn_on_op,
    restore_op,
    init_sync_op,
    repair_sync_op,
    update_sync_op
)
from node_cli.utils.print_formatters import (
    print_failed_requirements_checks, print_node_cmd_error, print_node_info
)
from node_cli.utils.helper import error_exit, get_request, post_request
from node_cli.utils.helper import extract_env_params
from node_cli.utils.texts import Texts
from node_cli.utils.exit_codes import CLIExitCodes
from node_cli.utils.decorators import (
    check_not_inited,
    check_inited,
    check_user
)


logger = logging.getLogger(__name__)
TEXTS = Texts()

SYNC_BASE_CONTAINERS_AMOUNT = 2
BASE_CONTAINERS_AMOUNT = 5
BLUEPRINT_NAME = 'node'


class NodeStatuses(Enum):
    """This class contains possible node statuses"""
    ACTIVE = 0
    LEAVING = 1
    FROZEN = 2
    IN_MAINTENANCE = 3
    LEFT = 4
    NOT_CREATED = 5


def is_update_safe() -> bool:
    status, payload = get_request(BLUEPRINT_NAME, 'update-safe')
    if status == 'error':
        return False
    safe = payload['update_safe']
    if not safe:
        logger.info('Locked schains: %s', payload['unsafe_chains'])
    return safe


@check_inited
@check_user
def register_node(name, p2p_ip,
                  public_ip, port, domain_name):

    if not is_node_inited():
        print(TEXTS['node']['not_inited'])
        return

    # todo: add name, ips and port checks
    json_data = {
        'name': name,
        'ip': p2p_ip,
        'publicIP': public_ip,
        'port': port,
        'domain_name': domain_name
    }
    status, payload = post_request(
        blueprint=BLUEPRINT_NAME,
        method='register',
        json=json_data
    )
    if status == 'ok':
        msg = TEXTS['node']['registered']
        logger.info(msg)
        print(msg)
    else:
        error_msg = payload
        logger.error(f'Registration error {error_msg}')
        error_exit(error_msg, exit_code=CLIExitCodes.BAD_API_RESPONSE)


@check_not_inited
def init(env_filepath):
    env = get_node_env(env_filepath)
    if env is None:
        return
    configure_firewall_rules()
    inited_ok = init_op(env_filepath, env)
    if not inited_ok:
        error_exit(
            'Init operation failed',
            exit_code=CLIExitCodes.OPERATION_EXECUTION_ERROR
        )
    logger.info('Waiting for containers initialization')
    time.sleep(TM_INIT_TIMEOUT)
    if not is_base_containers_alive():
        error_exit(
            'Containers are not running',
            exit_code=CLIExitCodes.OPERATION_EXECUTION_ERROR
        )
    logger.info('Generating resource allocation file ...')
    update_resource_allocation(env['ENV_TYPE'])
    logger.info('Init procedure finished')


@check_not_inited
def restore(backup_path, env_filepath, no_snapshot=False, config_only=False):
    env = get_node_env(env_filepath)
    if env is None:
        return
    save_env_params(env_filepath)
    env['SKALE_DIR'] = SKALE_DIR

    if not no_snapshot:
        logger.info('Adding BACKUP_RUN to env ...')
        env['BACKUP_RUN'] = 'True'  # should be str

    restored_ok = restore_op(env, backup_path, config_only=config_only)
    if not restored_ok:
        error_exit(
            'Restore operation failed',
            exit_code=CLIExitCodes.OPERATION_EXECUTION_ERROR
        )
    time.sleep(RESTORE_SLEEP_TIMEOUT)
    logger.info('Generating resource allocation file ...')
    update_resource_allocation(env['ENV_TYPE'])
    print('Node is restored from backup')


def init_sync(
    env_filepath: str,
    archive: bool,
    catchup: bool,
    historic_state: bool,
    snapshot_from: str
) -> None:
    configure_firewall_rules()
    env = get_node_env(env_filepath, sync_node=True)
    if env is None:
        return
    inited_ok = init_sync_op(
        env_filepath,
        env,
        archive,
        catchup,
        historic_state,
        snapshot_from
    )
    if not inited_ok:
        error_exit(
            'Init operation failed',
            exit_code=CLIExitCodes.OPERATION_EXECUTION_ERROR
        )
    logger.info('Waiting for containers initialization')
    time.sleep(TM_INIT_TIMEOUT)
    if not is_base_containers_alive(sync_node=True):
        error_exit(
            'Containers are not running',
            exit_code=CLIExitCodes.OPERATION_EXECUTION_ERROR
        )
    logger.info('Sync node initialized successfully')


@check_inited
@check_user
def update_sync(env_filepath: str, unsafe_ok: bool = False) -> None:
    logger.info('Node update started')
    configure_firewall_rules()
    env = get_node_env(env_filepath, sync_node=True)
    update_ok = update_sync_op(env_filepath, env)
    if update_ok:
        logger.info('Waiting for containers initialization')
        time.sleep(TM_INIT_TIMEOUT)
    alive = is_base_containers_alive(sync_node=True)
    if not update_ok or not alive:
        print_node_cmd_error()
        return
    else:
        logger.info('Node update finished')


@check_inited
@check_user
def repair_sync(
    archive: bool,
    catchup: bool,
    historic_state: bool,
    snapshot_from: str
) -> None:

    env_params = extract_env_params(INIT_ENV_FILEPATH, sync_node=True)
    schain_name = env_params['SCHAIN_NAME']
    repair_sync_op(
        schain_name=schain_name,
        archive=archive,
        catchup=catchup,
        historic_state=historic_state,
        snapshot_from=snapshot_from
    )
    logger.info('Schain was started from scratch')


def get_node_env(
    env_filepath,
    inited_node=False,
    sync_schains=None,
    pull_config_for_schain=None,
    sync_node=False
):
    if env_filepath is not None:
        env_params = extract_env_params(
            env_filepath,
            sync_node=sync_node,
            raise_for_status=True
        )
        save_env_params(env_filepath)
    else:
        env_params = extract_env_params(INIT_ENV_FILEPATH, sync_node=sync_node)

    mnt_dir = SCHAINS_MNT_DIR_SYNC if sync_node else SCHAINS_MNT_DIR_REGULAR
    env = {
        'SKALE_DIR': SKALE_DIR,
        'SCHAINS_MNT_DIR': mnt_dir,
        'FILESTORAGE_MAPPING': FILESTORAGE_MAPPING,
        'SKALE_LIB_PATH': SKALE_STATE_DIR,
        **env_params
    }
    if inited_node and not sync_node:
        flask_secret_key = get_flask_secret_key()
        env['FLASK_SECRET_KEY'] = flask_secret_key
    if sync_schains and not sync_node:
        env['BACKUP_RUN'] = 'True'
    if pull_config_for_schain:
        env['PULL_CONFIG_FOR_SCHAIN'] = pull_config_for_schain
    return {k: v for k, v in env.items() if v != ''}


@check_inited
@check_user
def update(env_filepath: str, pull_config_for_schain: str, unsafe_ok: bool = False) -> None:
    if not unsafe_ok and not is_update_safe():
        error_msg = 'Cannot update safely'
        error_exit(error_msg, exit_code=CLIExitCodes.UNSAFE_UPDATE)

    logger.info('Node update started')
    configure_firewall_rules()
    env = get_node_env(
        env_filepath,
        inited_node=True,
        sync_schains=False,
        pull_config_for_schain=pull_config_for_schain
    )
    update_ok = update_op(env_filepath, env)
    if update_ok:
        logger.info('Waiting for containers initialization')
        time.sleep(TM_INIT_TIMEOUT)
    alive = is_base_containers_alive()
    if not update_ok or not alive:
        print_node_cmd_error()
        return
    else:
        logger.info('Node update finished')


def get_node_signature(validator_id):
    params = {'validator_id': validator_id}
    status, payload = get_request(
        blueprint=BLUEPRINT_NAME,
        method='signature',
        params=params
    )
    if status == 'ok':
        return payload['signature']
    else:
        return payload


def backup(path):
    backup_filepath = get_backup_filepath(path)
    create_backup_archive(backup_filepath)


def get_backup_filename():
    time = datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
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
            logger.debug('Cheking if %s is parent of %s', e, tarinfo.name)
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
    pack_dir(
        SKALE_DIR,
        backup_filepath,
        exclude=(cli_log_path, container_log_path)
    )
    print(f'Backup archive succesfully created {backup_filepath}')


def set_maintenance_mode_on():
    print('Setting maintenance mode on...')
    status, payload = post_request(
        blueprint=BLUEPRINT_NAME,
        method='maintenance-on'
    )
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
    status, payload = post_request(
        blueprint=BLUEPRINT_NAME,
        method='maintenance-off'
    )
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
def turn_off(maintenance_on: bool = False, unsafe_ok: bool = False) -> None:
    if not unsafe_ok and not is_update_safe():
        error_msg = 'Cannot turn off safely'
        error_exit(error_msg, exit_code=CLIExitCodes.UNSAFE_UPDATE)
    if maintenance_on:
        set_maintenance_mode_on()
    turn_off_op()


@check_inited
@check_user
def turn_on(maintenance_off, sync_schains, env_file):
    env = get_node_env(env_file, inited_node=True, sync_schains=sync_schains)
    turn_on_op(env)
    logger.info('Waiting for containers initialization')
    time.sleep(TM_INIT_TIMEOUT)
    if not is_base_containers_alive():
        print_node_cmd_error()
        return
    logger.info('Node turned on')
    if maintenance_off:
        set_maintenance_mode_off()


def is_base_containers_alive(sync_node: bool = False):
    dclient = docker.from_env()
    containers = dclient.containers.list()
    skale_containers = list(filter(
        lambda c: c.name.startswith('skale_'), containers
    ))
    containers_amount = SYNC_BASE_CONTAINERS_AMOUNT if sync_node else BASE_CONTAINERS_AMOUNT
    return len(skale_containers) >= containers_amount


def get_node_info_plain():
    status, payload = get_request(
        blueprint=BLUEPRINT_NAME,
        method='info'
    )
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
        print_node_info(
            node_info,
            get_node_status(int(node_info['status']))
        )


def get_node_status(status):
    node_status = NodeStatuses(status).name
    return TEXTS['node']['status'][node_status]


@check_inited
def set_domain_name(domain_name):
    print(f'Setting new domain name: {domain_name}')
    status, payload = post_request(
        blueprint=BLUEPRINT_NAME,
        method='set-domain-name',
        json={
            'domain_name': domain_name
        }
    )
    if status == 'ok':
        msg = TEXTS['node']['domain_name_changed']
        logger.info(msg)
        print(msg)
    else:
        error_exit(payload, exit_code=CLIExitCodes.BAD_API_RESPONSE)


def run_checks(
    network: str = 'mainnet',
    container_config_path: str = CONTAINER_CONFIG_PATH,
    disk: Optional[str] = None
) -> None:
    if not is_node_inited():
        print(TEXTS['node']['not_inited'])
        return

    if disk is None:
        env = get_env_config()
        disk = env['DISK_MOUNTPOINT']
    failed_checks = run_host_checks(
        disk,
        network,
        container_config_path
    )
    if not failed_checks:
        print('Requirements checking succesfully finished!')
    else:
        print('Node is not fully meet the requirements!')
        print_failed_requirements_checks(failed_checks)


def configure_firewall_rules() -> None:
    print('Configuring firewall ...')
    configure_iptables()
    print('Done')
