#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
#
#   Copyright (C) 2019-Present SKALE Labs
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
from typing import Dict, List

from dotenv import load_dotenv

from node_cli.configs import SKALE_DIR, CONTAINER_CONFIG_PATH
from node_cli.configs.alias_address_validation import validate_env_alias_or_address, ContractType
from node_cli.utils.helper import error_exit

SKALE_DIR_ENV_FILEPATH = os.path.join(SKALE_DIR, '.env')
CONFIGS_ENV_FILEPATH = os.path.join(CONTAINER_CONFIG_PATH, '.env')

ALLOWED_ENV_TYPES = ['mainnet', 'testnet', 'qanet', 'devnet']

REQUIRED_PARAMS: Dict[str, str] = {
    'CONTAINER_CONFIGS_STREAM': '',
    'ENDPOINT': '',
    'MANAGER_CONTRACTS': '',
    'IMA_CONTRACTS': '',
    'FILEBEAT_HOST': '',
    'DISK_MOUNTPOINT': '',
    'SGX_SERVER_URL': '',
    'DOCKER_LVMPY_STREAM': '',
    'ENV_TYPE': '',
}

REQUIRED_PARAMS_SYNC: Dict[str, str] = {
    'SCHAIN_NAME': '',
    'CONTAINER_CONFIGS_STREAM': '',
    'ENDPOINT': '',
    'MANAGER_CONTRACTS': '',
    'IMA_CONTRACTS': '',
    'DISK_MOUNTPOINT': '',
    'DOCKER_LVMPY_STREAM': '',
    'ENV_TYPE': '',
}

OPTIONAL_PARAMS: Dict[str, str] = {
    'MONITORING_CONTAINERS': '',
    'TELEGRAF': '',
    'INFLUX_TOKEN': '',
    'INFLUX_URL': '',
    'TG_API_KEY': '',
    'TG_CHAT_ID': '',
    'CONTAINER_CONFIGS_DIR': '',
    'DISABLE_DRY_RUN': '',
    'DEFAULT_GAS_LIMIT': '',
    'DEFAULT_GAS_PRICE_WEI': '',
    'SKIP_DOCKER_CONFIG': '',
    'ENFORCE_BTRFS': '',
    'SKIP_DOCKER_CLEANUP': '',
}


def absent_required_params(params: Dict[str, str]) -> List[str]:
    return [key for key in params if key not in OPTIONAL_PARAMS and not params[key]]


def get_validated_env_config(
    env_filepath: str = SKALE_DIR_ENV_FILEPATH, sync_node: bool = False
) -> Dict[str, str]:
    load_env_file(env_filepath)
    params = build_env_params(sync_node)
    populate_env_params(params)
    validate_env_params(params)
    return params


def load_env_file(env_filepath: str) -> None:
    if not load_dotenv(dotenv_path=env_filepath):
        error_exit(f'Failed to load environment from {env_filepath}')


def build_env_params(sync_node: bool = False) -> Dict[str, str]:
    """Return environment variables dictionary with keys based on node type."""
    params = REQUIRED_PARAMS_SYNC.copy() if sync_node else REQUIRED_PARAMS.copy()
    params.update(OPTIONAL_PARAMS)
    return params


def populate_env_params(params: Dict[str, str]) -> None:
    for key in params:
        env_value = os.getenv(key)
        if env_value is not None:
            params[key] = str(env_value)


def validate_env_params(params: Dict[str, str]) -> None:
    missing = absent_required_params(params)
    if missing:
        error_exit(f'Missing required parameters: {missing}')
    validate_env_type(params['ENV_TYPE'])
    endpoint = params['ENDPOINT']
    validate_env_alias_or_address(params['IMA_CONTRACTS'], ContractType.IMA, endpoint)
    validate_env_alias_or_address(params['MANAGER_CONTRACTS'], ContractType.MANAGER, endpoint)


def validate_env_type(env_type: str) -> None:
    if env_type not in ALLOWED_ENV_TYPES:
        error_exit(f'Allowed ENV_TYPE values are {ALLOWED_ENV_TYPES}. Actual: "{env_type}"')
