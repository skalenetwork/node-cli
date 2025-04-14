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

import logging
import os
from shutil import copyfile
from urllib.parse import urlparse

from node_cli.core.resources import update_resource_allocation
from node_cli.utils.helper import error_exit

from node_cli.configs import (
    ADMIN_PORT,
    AUTOLOAD_KERNEL_MODULES_PATH,
    BTRFS_KERNEL_MODULE,
    DEFAULT_URL_SCHEME,
    NODE_DATA_PATH,
    SKALE_DIR,
    CONTAINER_CONFIG_PATH,
    CONTRACTS_PATH,
    ETH_STATE_PATH,
    NODE_CERTS_PATH,
    SGX_CERTS_PATH,
    REPORTS_PATH,
    REDIS_DATA_PATH,
    SCHAINS_DATA_PATH,
    LOG_PATH,
    REMOVED_CONTAINERS_FOLDER_PATH,
    SKALE_RUN_DIR,
    SKALE_STATE_DIR,
    SKALE_TMP_DIR,
    UFW_CONFIG_PATH,
    UFW_IPV6_BEFORE_INPUT_CHAIN,
)
from node_cli.configs.resource_allocation import RESOURCE_ALLOCATION_FILEPATH
from node_cli.configs.cli_logger import LOG_DATA_PATH
from node_cli.configs.env import SKALE_DIR_ENV_FILEPATH, CONFIGS_ENV_FILEPATH
from node_cli.core.nftables import NFTablesManager
from node_cli.utils.helper import safe_mkdir

from node_cli.utils.helper import safe_load_texts

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


def get_flask_secret_key() -> str:
    secret_key_filepath = os.path.join(NODE_DATA_PATH, 'flask_db_key.txt')

    if not os.path.exists(secret_key_filepath):
        error_exit(f'Flask secret key file not found at {secret_key_filepath}')

    try:
        with open(secret_key_filepath, 'r') as key_file:
            secret_key = key_file.read().strip()
            return secret_key
    except (IOError, OSError) as e:
        error_exit(f'Failed to read Flask secret key: {e}')


def prepare_host(env_filepath: str, env_type: str, allocation: bool = False) -> None:
    if not env_filepath or not env_type:
        error_exit('Missing required parameters for host initialization')

    try:
        logger.info('Preparing host started')
        make_dirs()
        save_env_params(env_filepath)

        if allocation:
            update_resource_allocation(env_type)
    except Exception as e:
        error_exit(f'Failed to prepare host: {str(e)}')


def is_node_inited() -> bool:
    return os.path.isfile(RESOURCE_ALLOCATION_FILEPATH)


def make_dirs():
    for dir_path in (
        SKALE_DIR,
        NODE_DATA_PATH,
        CONTAINER_CONFIG_PATH,
        CONTRACTS_PATH,
        ETH_STATE_PATH,
        NODE_CERTS_PATH,
        REMOVED_CONTAINERS_FOLDER_PATH,
        SGX_CERTS_PATH,
        SCHAINS_DATA_PATH,
        LOG_PATH,
        REPORTS_PATH,
        REDIS_DATA_PATH,
        SKALE_RUN_DIR,
        SKALE_STATE_DIR,
        SKALE_TMP_DIR,
    ):
        safe_mkdir(dir_path)


def save_env_params(env_filepath: str) -> None:
    copyfile(env_filepath, SKALE_DIR_ENV_FILEPATH)


def link_env_file():
    if not (os.path.islink(CONFIGS_ENV_FILEPATH) or os.path.isfile(CONFIGS_ENV_FILEPATH)):
        logger.info('Creating symlink %s → %s', SKALE_DIR_ENV_FILEPATH, CONFIGS_ENV_FILEPATH)
        os.symlink(SKALE_DIR_ENV_FILEPATH, CONFIGS_ENV_FILEPATH)


def init_logs_dir():
    safe_mkdir(LOG_DATA_PATH)
    safe_mkdir(REMOVED_CONTAINERS_FOLDER_PATH)


def init_data_dir():
    safe_mkdir(NODE_DATA_PATH)


def is_btrfs_module_autoloaded(modules_filepath=AUTOLOAD_KERNEL_MODULES_PATH):
    if not os.path.isfile(modules_filepath):
        return False
    with open(modules_filepath) as modules_file:
        modules = set(
            map(
                lambda line: line.strip(),
                filter(lambda line: not line.startswith('#'), modules_file.readlines()),
            )
        )
        return BTRFS_KERNEL_MODULE in modules


def add_btrfs_module_to_autoload(modules_filepath=AUTOLOAD_KERNEL_MODULES_PATH):
    with open(modules_filepath, 'a') as modules_file:
        modules_file.write(f'{BTRFS_KERNEL_MODULE}\n')


def ensure_btrfs_kernel_module_autoloaded(modules_filepath=AUTOLOAD_KERNEL_MODULES_PATH):
    logger.debug('Checking if btrfs is in %s', modules_filepath)
    if not is_btrfs_module_autoloaded(modules_filepath):
        logger.info('Adding btrfs module to %s', modules_filepath)
        add_btrfs_module_to_autoload(modules_filepath)
    else:
        logger.debug('btrfs is already in %s', modules_filepath)


def is_ufw_ipv6_option_enabled() -> bool:
    """Check if UFW is enabled and IPv6 is configured."""
    if os.path.isfile(UFW_CONFIG_PATH):
        with open(UFW_CONFIG_PATH, 'r') as file:
            for line in file:
                if line.startswith('IPV6='):
                    return line.strip().split('=')[1].strip() == 'yes'
    return False


def is_ufw_ipv6_chain_exists() -> bool:
    nft_manager = NFTablesManager(family='ip6', table='filter')
    return nft_manager.chain_exists(chain=UFW_IPV6_BEFORE_INPUT_CHAIN)
