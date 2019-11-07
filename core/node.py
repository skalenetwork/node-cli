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
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import logging
import requests
import subprocess
from configs import (INSTALL_SCRIPT, UNINSTALL_SCRIPT, UPDATE_SCRIPT, UPDATE_NODE_PROJECT_SCRIPT,
                     ROUTES)
from core.helper import get_node_creds, construct_url, post_request, print_err_response
from core.host import prepare_host, init_data_dir

logger = logging.getLogger(__name__)


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
        msg = 'Node registered in SKALE manager. For more info run: skale node info'
        logging.info(msg)
        print(msg)
    else:
        logging.info(response.json())
        print_err_response(response.json())


def init(mta_endpoint, git_branch, github_token, docker_username, docker_password, endpoint,
         db_user, db_password, db_root_password, db_port, disk_mountpoint, manager_url, ima_url,
         filebeat_url, test_mode):
    env = {
        **os.environ,
        'MTA_ENDPOINT': mta_endpoint,
        'GIT_BRANCH': git_branch,
        'GITHUB_TOKEN': github_token,
        'DOCKER_USERNAME': docker_username,
        'DOCKER_PASSWORD': str(docker_password),
        'ENDPOINT': endpoint,
        'DB_USER': db_user,
        'DB_PASSWORD': db_password,
        'DB_ROOT_PASSWORD': db_root_password,
        'DB_PORT': str(db_port),
        'DISK_MOUNTPOINT': disk_mountpoint,
        'MANAGER_CONTRACTS_INFO_URL': manager_url,
        'IMA_CONTRACTS_INFO_URL': ima_url,
        'FILEBEAT_HOST': filebeat_url,
    }
    init_data_dir()

    prepare_host(test_mode, disk_mountpoint)
    res = subprocess.run(['bash', INSTALL_SCRIPT], env=env)
    logging.info(f'Node init install script result: {res.stderr}, {res.stdout}')
    # todo: check execution result


def purge():
    # todo: check that node is installed
    subprocess.run(['sudo', 'bash', UNINSTALL_SCRIPT])
    # todo: check execution result


def deregister():
    pass


def update(ima_endpoint, github_token, docker_username, docker_password, endpoint, db_user,
           db_password, db_root_password, db_port, manager_url, ima_url, filebeat_url):
    env = {
        **os.environ,
        'IMA_ENDPOINT': ima_endpoint,
        'GITHUB_TOKEN': github_token,
        'DOCKER_USERNAME': docker_username,
        'DOCKER_PASSWORD': str(docker_password),
        'ENDPOINT': endpoint,
        'DB_USER': db_user,
        'DB_PASSWORD': db_password,
        'DB_ROOT_PASSWORD': db_root_password,
        'DB_PORT': str(db_port),
        'DISK_MOUNTPOINT': '/',
        'MANAGER_CONTRACTS_INFO_URL': manager_url,
        'IMA_CONTRACTS_INFO_URL': ima_url,
        'FILEBEAT_HOST': filebeat_url,
    }
    res_update_project = subprocess.run(['sudo', '-E', 'bash', UPDATE_NODE_PROJECT_SCRIPT], env=env)
    logging.info(
        f'Update node project script result: {res_update_project.stderr}, \
        {res_update_project.stdout}')
    res_update_node = subprocess.run(['sudo', '-E', 'bash', UPDATE_SCRIPT], env=env)
    logging.info(
        f'Update node script result: {res_update_node.stderr}, {res_update_node.stdout}')
    # todo: check execution result
