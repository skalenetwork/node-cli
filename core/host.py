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
import logging
import subprocess
import requests
from urllib.parse import urlparse

from core.resources import save_resource_allocation_config

from configs import DEPENDENCIES_SCRIPT, ROUTES, SKALE_NODE_UI_PORT, DEFAULT_URL_SCHEME, \
    INSTALL_CONVOY_SCRIPT, NODE_DATA_PATH
from configs.cli_logger import LOG_DATA_PATH
from configs.resource_allocation import DISK_MOUNTPOINT_FILEPATH, CONVOY_HELPER_SCRIPT_FILEPATH, \
    CONVOY_SERVICE_TEMPLATE_PATH, CONVOY_SERVICE_PATH, SGX_SERVER_URL_FILEPATH

from core.helper import safe_get_config, safe_load_texts, construct_url, clean_cookies, \
    clean_host, get_localhost_endpoint
from tools.helper import run_cmd, process_template

TEXTS = safe_load_texts()

logger = logging.getLogger(__name__)


def install_host_dependencies():
    env = {
        **os.environ,
        'SKALE_CMD': 'host_deps'
    }
    subprocess.run(["sudo", "bash", DEPENDENCIES_SCRIPT], env=env)
    # todo: check execution status


def show_host(config):
    host = safe_get_config(config, 'host')
    if host:
        print(f'SKALE node host: {host}')
    else:
        print(TEXTS['service']['no_node_host'])


def reset_host(config):
    clean_cookies(config)
    clean_host(config)
    logging.info(f'Resetting host to defaut: {get_localhost_endpoint()}')
    print('Host removed, cookies cleaned.')


def test_host(host):
    url = construct_url(host, ROUTES['test_host'])

    try:
        response = requests.get(url)
    except requests.exceptions.ConnectionError:
        return False  # todo: return different error messages
    except requests.exceptions.InvalidURL:
        return False  # todo: return different error messages

    return response.status_code == requests.codes.ok


def fix_url(url):
    try:
        result = urlparse(url)
        if not result.scheme:
            url = f'{DEFAULT_URL_SCHEME}{url}'
        if not url.endswith(str(SKALE_NODE_UI_PORT)):
            return f'{url}:{SKALE_NODE_UI_PORT}'
        return url
    except ValueError:
        return False


def prepare_host(test_mode, disk_mountpoint, sgx_server_url):
    logger.info(f'Preparing host started, disk_mountpoint: {disk_mountpoint}')
    save_disk_mountpoint(disk_mountpoint)
    save_sgx_server_url(sgx_server_url)
    save_resource_allocation_config()


def init_convoy(disk_mountpoint):
    print(f'Installing convoy...')
    run_cmd(['bash', INSTALL_CONVOY_SCRIPT], shell=False)
    print(f'Downloading convoy disk helper...')
    convoy_prepare_disk(disk_mountpoint)
    start_convoy_daemon(disk_mountpoint)


def start_convoy_daemon(disk_mountpoint):
    template_data = {
        # 'user': get_username(),
        'cmd': f'/usr/local/bin/convoy daemon --drivers devicemapper --driver-opts \
        dm.datadev={disk_mountpoint}1 --driver-opts dm.metadatadev={disk_mountpoint}2'
    }
    msg = f'Starting convoy daemon, template data: {template_data}'
    logger.info(msg), print(msg)
    process_template(CONVOY_SERVICE_TEMPLATE_PATH, CONVOY_SERVICE_PATH, template_data)
    run_cmd(['systemctl', 'enable', 'convoy'], shell=False)
    run_cmd(['systemctl', 'start', 'convoy'], shell=False)


def convoy_prepare_disk(disk_mountpoint):
    msg = 'Applying disk partitioning...'
    logger.info(msg), print(msg)
    run_cmd(['bash', CONVOY_HELPER_SCRIPT_FILEPATH, '--write-to-disk', f'{disk_mountpoint}'],
            shell=False)


def save_disk_mountpoint(disk_mountpoint):
    logger.info(f'Saving disk_mountpoint option to {DISK_MOUNTPOINT_FILEPATH}')
    with open(DISK_MOUNTPOINT_FILEPATH, 'w') as f:
        f.write(disk_mountpoint)


def save_sgx_server_url(sgx_server_url):
    logger.info(f'Saving disk_mountpoint option to {SGX_SERVER_URL_FILEPATH}')
    with open(SGX_SERVER_URL_FILEPATH, 'w') as f:
        f.write(sgx_server_url)


def init_logs_dir():
    safe_mk_dirs(LOG_DATA_PATH)


def init_data_dir():
    safe_mk_dirs(NODE_DATA_PATH)


def safe_mk_dirs(path):
    if os.path.exists(path):
        return
    msg = f'Creating {path} directory...'
    logger.info(msg), print(msg)
    os.makedirs(path, exist_ok=True)
