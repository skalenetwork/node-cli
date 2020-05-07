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


import logging
import subprocess

import click

from configs import (SKALE_DIR, INSTALL_SCRIPT, UNINSTALL_SCRIPT,
                     UPDATE_SCRIPT, DATAFILES_FOLDER)

from configs.env import (absent_params as absent_env_params,
                         get_params as get_env_params)
from core.helper import get_request, post_request
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


def extract_env_params(env_filepath):
    env_params = get_env_params(env_filepath)

    if not env_params.get('DB_ROOT_PASSWORD'):
        env_params['DB_ROOT_PASSWORD'] = env_params['DB_PASSWORD']

    absent_params = ', '.join(absent_env_params(env_params))
    if absent_params:
        click.echo(f"Your env file({env_filepath}) have some absent params: "
                   f"{absent_params}.\n"
                   f"You should specify them to make sure that "
                   f"all services are working",
                   err=True)
        return None
    return env_params


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


def purge():
    # todo: check that node is installed
    subprocess.run(['sudo', 'bash', UNINSTALL_SCRIPT])
    # todo: check execution result


def deregister():
    pass


def update(env_filepath):
    if env_filepath is not None:
        env_params = extract_env_params(env_filepath)
        if env_params is None:
            return
        save_env_params(env_filepath)
    else:
        env_params = {}

    flask_secret_key = get_flask_secret_key()
    res_update_node = subprocess.run(['bash', UPDATE_SCRIPT], env={
        'SKALE_DIR': SKALE_DIR,
        'FLASK_SECRET_KEY': flask_secret_key,
        'DATAFILES_FOLDER': DATAFILES_FOLDER,
        **env_params
    })
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
