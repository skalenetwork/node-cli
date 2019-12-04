#   -*- coding: utf-8 -*-
#
#   This file is part of skale-node-cli
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

import logging
import os
import requests
import subprocess


import click
from configs import (INSTALL_SCRIPT, UNINSTALL_SCRIPT, UPDATE_SCRIPT,
                     UPDATE_NODE_PROJECT_SCRIPT,
                     ROUTES)
from configs.env import settings as env_settings
from core.helper import (get_node_creds, construct_url,
                         post_request, print_err_response)
from core.host import prepare_host, init_data_dir

logger = logging.getLogger(__name__)


def apsent_env_params(params):
    return filter(lambda key: not params[key], params)


def create_node(config, name, p2p_ip, public_ip, port):
    # todo: add name, ips and port checks
    host, cookies = get_node_creds(config)
    data = {
        'name': name,
        'ip': p2p_ip,
        'publicIP': public_ip,
        'port': port
    }
    url = construct_url(host, ROUTES['create_node'])
    try:  # todo: tmp fix!
        response = post_request(url, data, cookies)
    except Exception:
        response = post_request(url, data, cookies)

    if response is None:
        print('Your request returned nothing. Something went wrong. Try again')
        return None
    if response.status_code == requests.codes.created:
        msg = 'Node registered in SKALE manager. ' \
              'For more info run: skale node info'
        logging.info(msg)
        print(msg)
    else:
        logging.info(response.json())
        print_err_response(response.json())


def init(disk_mountpoint, test_mode, sgx_server_url):
    env_params = {
        **os.environ,
        **env_settings,
        'DISK_MOUNTPOINT': disk_mountpoint,
        'SGX_SERVER_URL': sgx_server_url,
    }
    if not env_params.get('DB_ROOT_PASSWORD'):
        env_params['DB_ROOT_PASSWORD'] = env_params['DB_PASSWORD']

    apsent_params = ', '.join(apsent_env_params(env_params))
    if apsent_params:
        click.echo(f"You have not specified some options through .env file: "
                   f"{apsent_params}. "
                   f"Some services will not work", err=True)

    init_data_dir()
    prepare_host(test_mode, disk_mountpoint, sgx_server_url)
    res = subprocess.run(['bash', INSTALL_SCRIPT], env=env_params)
    logging.info(f'Node init install script result: {res.stderr}, {res.stdout}')
    # todo: check execution result


def purge():
    # todo: check that node is installed
    subprocess.run(['sudo', 'bash', UNINSTALL_SCRIPT])
    # todo: check execution result


def deregister():
    pass


def update():
    env_params = {
        **os.environ,
        **env_settings,
        'DISK_MOUNTPOINT': '/',
    }
    if not env_params.get('DB_ROOT_PASSWORD'):
        env_params['DB_ROOT_PASSWORD'] = env_params['DB_PASSWORD']

    apsent_params = ', '.join(apsent_env_params(env_params))
    if apsent_params:
        click.echo(f"You have not specified the following options "
                   f"through .env file: {apsent_params} "
                   f"Some services won't work")
    res_update_project = subprocess.run(
        ['sudo', '-E', 'bash', UPDATE_NODE_PROJECT_SCRIPT],
        env=env_params
    )
    logging.info(
        f'Update node project script result: {res_update_project.stderr}, \
        {res_update_project.stdout}')
    res_update_node = subprocess.run(
        ['sudo', '-E', 'bash', UPDATE_SCRIPT],
        env=env_params,
    )
    logging.info(
        f'Update node script result: '
        f'{res_update_node.stderr}, {res_update_node.stdout}')
    # todo: check execution result
