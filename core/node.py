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
import shlex
import subprocess
import time
from enum import Enum

import docker

from cli.info import VERSION
from configs import (SKALE_DIR, INSTALL_SCRIPT, UNINSTALL_SCRIPT,
                     BACKUP_INSTALL_SCRIPT,
                     UPDATE_SCRIPT, DATAFILES_FOLDER, INIT_ENV_FILEPATH,
                     BACKUP_ARCHIVE_NAME, HOME_DIR, RESTORE_SLEEP_TIMEOUT,
                     TURN_OFF_SCRIPT, TURN_ON_SCRIPT, TM_INIT_TIMEOUT)
from configs.cli_logger import LOG_DIRNAME

from core.helper import get_request, post_request
from core.mysql_backup import create_mysql_backup, restore_mysql_backup
from core.host import (is_node_inited, prepare_host,
                       save_env_params, get_flask_secret_key)
from core.print_formatters import print_err_response, print_node_cmd_error, print_node_info
from core.resources import update_resource_allocation
from tools.meta import update_meta
from tools.helper import run_cmd, extract_env_params
from tools.texts import Texts

logger = logging.getLogger(__name__)
TEXTS = Texts()

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


def register_node(config, name, p2p_ip,
                  public_ip, port, gas_limit=None,
                  gas_price=None,
                  skip_dry_run=False):
    # todo: add name, ips and port checks
    json_data = {
        'name': name,
        'ip': p2p_ip,
        'publicIP': public_ip,
        'port': port,
        'gas_limit': gas_limit,
        'gas_price': gas_price,
        'skip_dry_run': skip_dry_run
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
        print_err_response(error_msg)


def init(env_filepath, dry_run=False):
    if is_node_inited():
        print(TEXTS['node']['already_inited'])
        return
    env_params = extract_env_params(env_filepath)
    if env_params is None:
        return
    prepare_host(
        env_filepath,
        env_params['DISK_MOUNTPOINT'],
        env_params['SGX_SERVER_URL']
    )
    update_meta(VERSION, env_params['CONTAINER_CONFIGS_STREAM'])
    dry_run = 'yes' if dry_run else ''
    env = {
        'SKALE_DIR': SKALE_DIR,
        'DATAFILES_FOLDER': DATAFILES_FOLDER,
        'DRY_RUN': dry_run,
        **env_params
    }
    try:
        run_cmd(['bash', INSTALL_SCRIPT], env=env)
    except Exception:
        logger.exception('Install script process errored')
        print_node_cmd_error()
        return
    print('Waiting for transaction manager initialization ...')
    time.sleep(TM_INIT_TIMEOUT)
    if not is_base_containers_alive():
        print_node_cmd_error()
        return
    logger.info('Generating resource allocation file ...')
    update_resource_allocation()
    print('Init procedure finished')


def restore(backup_path, env_filepath):
    env_params = extract_env_params(env_filepath)
    if env_params is None:
        return
    save_env_params(env_filepath)
    if not run_restore_script(backup_path, env_params):
        return
    time.sleep(RESTORE_SLEEP_TIMEOUT)
    if not restore_mysql_backup(env_filepath):
        print('WARNING: MySQL data restoring failed. '
              'Check < skale logs cli > for more information')
    print('Node is restored from backup')


def run_restore_script(backup_path, env_params) -> bool:
    env = {
        'SKALE_DIR': SKALE_DIR,
        'DATAFILES_FOLDER': DATAFILES_FOLDER,
        'BACKUP_RUN': 'True',
        'BACKUP_PATH': backup_path,
        'HOME_DIR': HOME_DIR,
        **env_params
    }
    try:
        run_cmd(['bash', BACKUP_INSTALL_SCRIPT], env=env)
    except Exception:
        logger.exception('Restore script process errored')
        print_node_cmd_error()
        return False
    return True


def purge():
    # todo: check that node is installed
    run_cmd(['sudo', 'bash', UNINSTALL_SCRIPT])
    print('Success')


def get_inited_node_env(env_filepath, sync_schains):
    if env_filepath is not None:
        env_params = extract_env_params(env_filepath)
        if env_params is None:
            return
        save_env_params(env_filepath)
    else:
        env_params = extract_env_params(INIT_ENV_FILEPATH)
    flask_secret_key = get_flask_secret_key()
    env = {
        'SKALE_DIR': SKALE_DIR,
        'FLASK_SECRET_KEY': flask_secret_key,
        'DATAFILES_FOLDER': DATAFILES_FOLDER,
        **env_params
    }
    if sync_schains:
        env['BACKUP_RUN'] = 'True'
    return env


def update(env_filepath, sync_schains):
    if not is_node_inited():
        print(TEXTS['node']['not_inited'])
        return

    print('Updating the node...')
    env = get_inited_node_env(env_filepath, sync_schains)
    prepare_host(
        env_filepath,
        env['DISK_MOUNTPOINT'],
        env['SGX_SERVER_URL'],
        allocation=True
    )
    update_meta(VERSION, env['CONTAINER_CONFIGS_STREAM'])
    try:
        run_cmd(['bash', UPDATE_SCRIPT], env=env)
    except Exception:
        logger.exception('Update script process errored')
        print_node_cmd_error()
        return
    print('Waiting for transaction manager initialization ...')
    time.sleep(TM_INIT_TIMEOUT)
    if not is_base_containers_alive():
        print_node_cmd_error()
        return
    print('Update procedure finished')


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


def backup(path, env_filepath, mysql_backup=True):
    if mysql_backup:
        if not create_mysql_backup(env_filepath):
            print('Something went wrong while trying to create MySQL backup, '
                  'check out < skale logs cli > output')
            return
    backup_filepath = get_backup_filepath(path)
    create_backup_archive(backup_filepath)


def get_backup_filename():
    time = datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
    return f'{BACKUP_ARCHIVE_NAME}-{time}.tar.gz'


def get_backup_filepath(base_path):
    return os.path.join(base_path, get_backup_filename())


def create_backup_archive(backup_filepath):
    print('Creating backup archive...')
    log_skale_path = os.path.join('.skale', LOG_DIRNAME)
    cmd = shlex.split(
        f'tar -zcvf {backup_filepath} -C {HOME_DIR} '
        f'--exclude {log_skale_path} .skale'
    )
    try:
        run_cmd(cmd)
        print(f'Backup archive succesfully created: {backup_filepath}')
    except subprocess.CalledProcessError:
        logger.exception('Backup archive creation failed')
        print_node_cmd_error()


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
        print_err_response(error_msg)


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
        print_err_response(error_msg)


def run_turn_off_script():
    print('Turing off the node...')
    cmd_env = {
        'SKALE_DIR': SKALE_DIR,
        'DATAFILES_FOLDER': DATAFILES_FOLDER
    }
    try:
        run_cmd(['bash', TURN_OFF_SCRIPT], env=cmd_env)
    except Exception:
        logger.exception('Turning off failed')
        print_node_cmd_error()
        return
    print('Node was successfully turned off')


def run_turn_on_script(sync_schains, env_filepath):
    print('Turning on the node...')
    env = get_inited_node_env(env_filepath, sync_schains)
    try:
        run_cmd(['bash', TURN_ON_SCRIPT], env=env)
    except Exception:
        logger.exception('Turning on failed')
        print_node_cmd_error()
        return
    print('Waiting for transaction manager initialization ...')
    time.sleep(TM_INIT_TIMEOUT)
    print('Node was successfully turned on')


def turn_off(maintenance_on):
    if not is_node_inited():
        print(TEXTS['node']['not_inited'])
        return
    if maintenance_on:
        set_maintenance_mode_on()
    run_turn_off_script()


def turn_on(maintenance_off, sync_schains, env_file):
    if not is_node_inited():
        print(TEXTS['node']['not_inited'])
        return
    run_turn_on_script(sync_schains, env_file)
    # TODO: Handle error from turn on script
    if maintenance_off:
        set_maintenance_mode_off()


def is_base_containers_alive():
    dclient = docker.from_env()
    containers = dclient.containers.list()
    skale_containers = list(filter(
        lambda c: c.name.startswith('skale_'), containers
    ))
    return len(skale_containers) >= BASE_CONTAINERS_AMOUNT


def get_node_info(config, format):
    status, payload = get_request(
        blueprint=BLUEPRINT_NAME,
        method='info'
    )
    if status == 'ok':
        node_info = payload['node_info']
        if format == 'json':
            print(node_info)
        elif node_info['status'] == NodeStatuses.NOT_CREATED.value:
            print(TEXTS['service']['node_not_registered'])
        else:
            print_node_info(node_info, get_node_status(int(node_info['status'])))
    else:
        print_err_response(payload)


def get_node_status(status):
    node_status = NodeStatuses(status).name
    return TEXTS['node']['status'][node_status]
