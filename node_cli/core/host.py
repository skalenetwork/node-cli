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

import json
import logging
import os
from shutil import copyfile
from urllib.parse import urlparse

from node_cli.core.resources import update_resource_allocation
from node_cli.core.checks import (
    get_requirements, DockerChecker, ListChecks,
    MachineChecker, PackagesChecker
)

from node_cli.configs import (
    ADMIN_PORT, DEFAULT_URL_SCHEME, NODE_DATA_PATH,
    SKALE_DIR, CONTAINER_CONFIG_PATH, CONTRACTS_PATH,
    ETH_STATE_PATH, NODE_CERTS_PATH, SGX_CERTS_PATH,
    REDIS_DATA_PATH, SCHAINS_DATA_PATH, LOG_PATH,
    MYSQL_BACKUP_FOLDER, REMOVED_CONTAINERS_FOLDER_PATH,
    IMA_CONTRACTS_FILEPATH, MANAGER_CONTRACTS_FILEPATH
)
from node_cli.configs.resource_allocation import RESOURCE_ALLOCATION_FILEPATH
from node_cli.configs.cli_logger import LOG_DATA_PATH
from node_cli.configs.env import SKALE_DIR_ENV_FILEPATH, CONFIGS_ENV_FILEPATH
from node_cli.utils.print_formatters import print_abi_validation_errors
from node_cli.configs.resource_allocation import (DISK_MOUNTPOINT_FILEPATH,
                                                  SGX_SERVER_URL_FILEPATH)

from node_cli.utils.helper import safe_load_texts, validate_abi

TEXTS = safe_load_texts()

logger = logging.getLogger(__name__)


def fix_url(url):
    try:
        result = urlparse(url)
        if not result.scheme:
            url = f'{DEFAULT_URL_SCHEME}{url}'
        if not url.endswith(str(ADMIN_PORT)):
            return f'{url}:{ADMIN_PORT}'
        return url
    except ValueError:
        return False


def get_flask_secret_key():
    secret_key_filepath = os.path.join(NODE_DATA_PATH, 'flask_db_key.txt')
    with open(secret_key_filepath) as key_file:
        return key_file.read().strip()


def prepare_host(env_filepath, disk_mountpoint, sgx_server_url, env_type,
                 allocation=False):
    logger.info(f'Preparing host started, disk_mountpoint: {disk_mountpoint}')
    make_dirs()
    save_env_params(env_filepath)
    save_disk_mountpoint(disk_mountpoint)
    save_sgx_server_url(sgx_server_url)
    if allocation:
        update_resource_allocation(env_type)


def run_preinstall_checks(network: str = 'mainnet') -> ListChecks:
    requirements = get_requirements(network)
    checkers = [
        MachineChecker(requirements),
        PackagesChecker(requirements),
        DockerChecker()
    ]
    result = []
    for checker in checkers:
        result.extend(filter(lambda r: r.status == 'error', checker.check()))
    return result


def is_node_inited():
    return os.path.isfile(RESOURCE_ALLOCATION_FILEPATH)


def make_dirs():
    for dir_path in (
            SKALE_DIR, NODE_DATA_PATH, CONTAINER_CONFIG_PATH,
            CONTRACTS_PATH, ETH_STATE_PATH, NODE_CERTS_PATH,
            MYSQL_BACKUP_FOLDER, REMOVED_CONTAINERS_FOLDER_PATH,
            SGX_CERTS_PATH, SCHAINS_DATA_PATH, LOG_PATH, REDIS_DATA_PATH
    ):
        safe_mk_dirs(dir_path)


def save_disk_mountpoint(disk_mountpoint):
    logger.info(f'Saving disk_mountpoint option to {DISK_MOUNTPOINT_FILEPATH}')
    with open(DISK_MOUNTPOINT_FILEPATH, 'w') as f:
        f.write(disk_mountpoint)


def save_sgx_server_url(sgx_server_url):
    logger.info(f'Saving disk_mountpoint option to {SGX_SERVER_URL_FILEPATH}')
    with open(SGX_SERVER_URL_FILEPATH, 'w') as f:
        f.write(sgx_server_url)


def save_env_params(env_filepath):
    copyfile(env_filepath, SKALE_DIR_ENV_FILEPATH)


def link_env_file():
    if not (os.path.islink(CONFIGS_ENV_FILEPATH) or os.path.isfile(CONFIGS_ENV_FILEPATH)):
        logger.info(f'Creating symlink {SKALE_DIR_ENV_FILEPATH} → {CONFIGS_ENV_FILEPATH}')
        os.symlink(SKALE_DIR_ENV_FILEPATH, CONFIGS_ENV_FILEPATH)


def init_logs_dir():
    safe_mk_dirs(LOG_DATA_PATH)
    safe_mk_dirs(REMOVED_CONTAINERS_FOLDER_PATH)


def init_data_dir():
    safe_mk_dirs(NODE_DATA_PATH)


def safe_mk_dirs(path, print_res=False):
    if os.path.exists(path):
        return
    msg = f'Creating {path} directory...'
    logger.info(msg)
    if print_res:
        print(msg)
    os.makedirs(path, exist_ok=True)


def validate_abi_files(json_result=False):
    results = [
        validate_abi(abi_filepath)
        for abi_filepath in [
            MANAGER_CONTRACTS_FILEPATH,
            IMA_CONTRACTS_FILEPATH
        ]
    ]
    if any(r['status'] == 'error' for r in results):
        print('Some files do not exist or are incorrect')
        print_abi_validation_errors(results, raw=json_result)
    else:
        if json_result:
            print(json.dumps({'result': 'ok'}))
        else:
            print('All abi files are correct json files!')
