#   -*- coding: utf-8 -*-
#
#   This file is part of skale-node-cli
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

import os
import shlex
import logging
import datetime
import subprocess

from configs import (SKALE_DIR, INSTALL_SCRIPT, UNINSTALL_SCRIPT, BACKUP_INSTALL_SCRIPT,
                     UPDATE_SCRIPT, DATAFILES_FOLDER, INIT_ENV_FILEPATH,
                     BACKUP_ARCHIVE_NAME, HOME_DIR)


from core.helper import get_request, post_request
from tools.helper import run_cmd, extract_env_params
from core.mysql_backup import create_mysql_backup, restore_mysql_backup
from core.host import prepare_host, save_env_params, get_flask_secret_key
from core.print_formatters import print_err_response
from tools.texts import Texts

logger = logging.getLogger(__name__)
TEXTS = Texts()


def register_node(config, name, p2p_ip, public_ip, port):
    # todo: add name, ips and port checks
    json_data = {
        'name': name,
        'ip': p2p_ip,
        'publicIP': public_ip,
        'port': port
    }
    status, payload = post_request('create_node',
                                   json=json_data)
    if status == 'ok':
        msg = TEXTS['node']['registered']
        logger.info(msg)
        print(msg)
    else:
        error_msg = payload
        logger.error(f'Registration error {error_msg}')
        print_err_response(error_msg)


def init(env_filepath, dry_run=False):
    env_params = extract_env_params(env_filepath)
    if env_params is None:
        return
    prepare_host(
        env_filepath,
        env_params['DISK_MOUNTPOINT'],
        env_params['SGX_SERVER_URL']
    )
    dry_run = 'yes' if dry_run else ''
    res = subprocess.run(['bash', INSTALL_SCRIPT], env={
        'SKALE_DIR': SKALE_DIR,
        'DATAFILES_FOLDER': DATAFILES_FOLDER,
        'DRY_RUN': dry_run,
        **env_params
    })
    logger.info(f'Node init install script result: {res.stderr}, {res.stdout}')
    # todo: check execution result


def restore(backup_path, env_filepath):
    env_params = extract_env_params(env_filepath)
    if env_params is None:
        return
    save_env_params(env_filepath)
    if not run_restore_script(backup_path, env_params):
        return
    if not restore_mysql_backup(env_filepath):
        return
    print('Node succesfully restored from backup')


def run_restore_script(backup_path, env_params) -> bool:
    res = subprocess.run(['bash', BACKUP_INSTALL_SCRIPT], env={
        'SKALE_DIR': SKALE_DIR,
        'DATAFILES_FOLDER': DATAFILES_FOLDER,
        'BACKUP_RUN': 'True',
        'BACKUP_PATH': backup_path,
        'HOME_DIR': HOME_DIR,
        **env_params
    })
    logger.info(f'Node restore from backup script result: {res.stderr}, {res.stdout}')
    if res.returncode != 0:
        print('Restore script failed, check node-cli logs')
        return False
    else:
        return True


def purge():
    # todo: check that node is installed
    subprocess.run(['sudo', 'bash', UNINSTALL_SCRIPT])
    # todo: check execution result


def deregister():
    pass


def update(env_filepath, sync_schains):
    if env_filepath is not None:
        env_params = extract_env_params(env_filepath)
        if env_params is None:
            return
        save_env_params(env_filepath)
    else:
        env_params = extract_env_params(INIT_ENV_FILEPATH)

    prepare_host(
        env_filepath,
        env_params['DISK_MOUNTPOINT'],
        env_params['SGX_SERVER_URL']
    )
    flask_secret_key = get_flask_secret_key()
    update_cmd_env = {
        'SKALE_DIR': SKALE_DIR,
        'FLASK_SECRET_KEY': flask_secret_key,
        'DATAFILES_FOLDER': DATAFILES_FOLDER,
        **env_params
    }
    if sync_schains:
        update_cmd_env['BACKUP_RUN'] = 'True'

    res_update_node = subprocess.run(['bash', UPDATE_SCRIPT], env=update_cmd_env)
    logger.info(
        f'Update node script result: '
        f'{res_update_node.stderr}, {res_update_node.stdout}')
    # todo: check execution result


def get_node_signature(validator_id):
    params = {'validator_id': validator_id}
    status, payload = get_request('node_signature', params=params)
    if status == 'ok':
        return payload['signature']
    else:
        return payload


def backup(path, env_filepath):
    if not create_mysql_backup(env_filepath):
        return
    backup_filepath = get_backup_filepath(path)
    create_backup_archive(backup_filepath)


def get_backup_filename():
    time = datetime.datetime.utcnow().strftime("%Y-%m-%d-%H:%M:%S")
    return f'{BACKUP_ARCHIVE_NAME}-{time}.tar.gz'


def get_backup_filepath(base_path):
    return os.path.join(base_path, get_backup_filename())


def create_backup_archive(backup_filepath):
    print('Creating backup archive...')
    cmd = shlex.split(f'tar -zcvf {backup_filepath} -C {HOME_DIR} .skale')
    try:
        run_cmd(cmd)
        print(f'Backup archive succesfully created: {backup_filepath}')
    except subprocess.CalledProcessError as e:
        logger.error(e)
        print('Something went wrong while trying to create backup archive, check out CLI logs')


def set_maintenance_mode_on():
    pass


def set_maintenance_mode_off():
    pass
