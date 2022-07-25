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

from node_cli.configs import (
    ADMIN_PORT, DEFAULT_URL_SCHEME, NODE_DATA_PATH,
    SKALE_DIR, CONTAINER_CONFIG_PATH, CONTRACTS_PATH,
    ETH_STATE_PATH, NODE_CERTS_PATH, SGX_CERTS_PATH,
    REPORTS_PATH, REDIS_DATA_PATH,
    SCHAINS_DATA_PATH, LOG_PATH,
    REMOVED_CONTAINERS_FOLDER_PATH,
    IMA_CONTRACTS_FILEPATH, MANAGER_CONTRACTS_FILEPATH,
    SKALE_RUN_DIR, SKALE_STATE_DIR, SKALE_TMP_DIR
)
from node_cli.configs.resource_allocation import (
    RESOURCE_ALLOCATION_FILEPATH
)
from node_cli.configs.cli_logger import LOG_DATA_PATH
from node_cli.configs.env import SKALE_DIR_ENV_FILEPATH, CONFIGS_ENV_FILEPATH
from node_cli.utils.helper import safe_mkdir
from node_cli.utils.print_formatters import print_abi_validation_errors

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


def prepare_host(
    env_filepath: str,
    env_type: str,
    allocation: bool = False
):
    logger.info(f'Preparing host started')
    make_dirs()
    save_env_params(env_filepath)

    if allocation:
        update_resource_allocation(env_type)


def is_node_inited():
    return os.path.isfile(RESOURCE_ALLOCATION_FILEPATH)


def make_dirs():
    for dir_path in (
            SKALE_DIR, NODE_DATA_PATH, CONTAINER_CONFIG_PATH,
            CONTRACTS_PATH, ETH_STATE_PATH, NODE_CERTS_PATH,
            REMOVED_CONTAINERS_FOLDER_PATH,
            SGX_CERTS_PATH, SCHAINS_DATA_PATH, LOG_PATH,
            REPORTS_PATH, REDIS_DATA_PATH,
            SKALE_RUN_DIR, SKALE_STATE_DIR, SKALE_TMP_DIR
    ):
        safe_mkdir(dir_path)


def save_env_params(env_filepath):
    copyfile(env_filepath, SKALE_DIR_ENV_FILEPATH)


def link_env_file():
    if not (os.path.islink(CONFIGS_ENV_FILEPATH) or
            os.path.isfile(CONFIGS_ENV_FILEPATH)):
        logger.info(
            'Creating symlink %s → %s',
            SKALE_DIR_ENV_FILEPATH, CONFIGS_ENV_FILEPATH
        )
        os.symlink(SKALE_DIR_ENV_FILEPATH, CONFIGS_ENV_FILEPATH)


def init_logs_dir():
    safe_mkdir(LOG_DATA_PATH)
    safe_mkdir(REMOVED_CONTAINERS_FOLDER_PATH)


def init_data_dir():
    safe_mkdir(NODE_DATA_PATH)


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
