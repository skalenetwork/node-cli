#   -*- coding: utf-8 -*-
#
#   This file is part of skale-node-cli
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.


import os
import logging
import subprocess

import click

from configs import (HOME_DIR, INSTALL_SCRIPT, UNINSTALL_SCRIPT,
                     UPDATE_SCRIPT, DATAFILES_FOLDER)

from configs.env import get_params
from core.helper import get_node_creds, post
from core.host import prepare_host
from tools.texts import Texts

logger = logging.getLogger(__name__)
TEXTS = Texts()


def apsent_env_params(params):
    return filter(lambda key: not params[key], params)


def register_node(config, name, p2p_ip, public_ip, port):
    # todo: add name, ips and port checks
    host, cookies = get_node_creds(config)
    json_data = {
        'name': name,
        'ip': p2p_ip,
        'publicIP': public_ip,
        'port': port
    }
    response = post('create_node', json=json_data)
    if response is None:
        print(TEXTS['service']['empty_response'])
        return None
    if response.get('errors') is not None:
        print(f'Node registration failed with error: {response["errors"]}')
        logger.error(f'Registration error {response["errors"]}')
        return
    if response['res']:
        msg = TEXTS['node']['registered']
        logger.info(msg)
        print(msg)
    else:
        logger.info('Bad response. Something went wrong. Try again')


def init(env_filepath, dry_run=False):
    env_params = get_params(env_filepath)

    if not env_params.get('DB_ROOT_PASSWORD'):
        env_params['DB_ROOT_PASSWORD'] = env_params['DB_PASSWORD']

    apsent_params = ', '.join(apsent_env_params(env_params))
    if apsent_params:
        click.echo(f"Your env file({env_filepath}) have some apsent params: "
                   f"{apsent_params}.\n"
                   f"You should specify them to make sure that "
                   f"all services are working",
                   err=True)
        return
    prepare_host(
        env_filepath,
        env_params['DISK_MOUNTPOINT'],
        env_params['SGX_SERVER_URL']
    )
    dry_run = 'yes' if dry_run else ''
    res = subprocess.run(['bash', INSTALL_SCRIPT], env={
        'HOME': HOME_DIR,
        'DATAFILES_FOLDER': DATAFILES_FOLDER,
        'GIT_BRANCH': env_params['GIT_BRANCH'],
        'GITHUB_TOKEN': env_params['GITHUB_TOKEN'],
        'DRY_RUN': dry_run,
        'DISK_MOUNTPOINT': env_params['DISK_MOUNTPOINT'],
        'MANAGER_CONTRACTS_INFO_URL': env_params['MANAGER_CONTRACTS_INFO_URL'],
        'IMA_CONTRACTS_INFO_URL': env_params['IMA_CONTRACTS_INFO_URL'],
        'DOCKER_USERNAME': env_params['DOCKER_USERNAME'],
        'DOCKER_PASSWORD': env_params['DOCKER_PASSWORD']
    })
    logging.info(f'Node init install script result: {res.stderr}, {res.stdout}')
    # todo: check execution result


def purge():
    # todo: check that node is installed
    subprocess.run(['sudo', 'bash', UNINSTALL_SCRIPT])
    # todo: check execution result


def deregister():
    pass


def update(env_filepath):
    params_from_file = get_params(env_filepath)
    env_params = {
        **params_from_file,
        'DISK_MOUNTPOINT': '/',
    }
    if not env_params.get('DB_ROOT_PASSWORD'):
        env_params['DB_ROOT_PASSWORD'] = env_params['DB_PASSWORD']

    apsent_params = ', '.join(apsent_env_params(env_params))
    if apsent_params:
        click.echo(f"Your env file({env_filepath}) have some apsent params: "
                   f"{apsent_params}.\n"
                   f"You should specify them to make sure that "
                   f"all services are working",
                   err=True)
        return
    # todo: extract only needed parameters
    env_params.update({
        **os.environ
    })
    res_update_node = subprocess.run(
        ['sudo', '-E', 'bash', UPDATE_SCRIPT],
        env=env_params,
    )
    logger.info(
        f'Update node script result: '
        f'{res_update_node.stderr}, {res_update_node.stdout}')
    # todo: check execution result
