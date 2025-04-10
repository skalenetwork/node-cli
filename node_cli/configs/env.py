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
from typing import Dict, List, Optional
from dotenv import load_dotenv
import requests
from enum import Enum

from node_cli.configs import SKALE_DIR, CONTAINER_CONFIG_PATH
from node_cli.utils.helper import error_exit, is_contract_address
from node_cli.utils.exit_codes import CLIExitCodes

SKALE_DIR_ENV_FILEPATH = os.path.join(SKALE_DIR, '.env')
CONFIGS_ENV_FILEPATH = os.path.join(CONTAINER_CONFIG_PATH, '.env')

ALLOWED_ENV_TYPES = ['mainnet', 'testnet', 'qanet', 'devnet']


class ContractType(Enum):
    """Contract types supported by the system with skale-contracts integration."""

    IMA = 'mainnet-ima'
    MANAGER = 'skale-manager'


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

METADATA_URL: str = (
    'https://raw.githubusercontent.com/skalenetwork/skale-contracts/'
    'refs/heads/deployments/metadata.json'
)


def absent_params(params: Dict[str, str]) -> List[str]:
    """Return a list of required parameters that are missing or empty."""
    return [key for key in params if key not in OPTIONAL_PARAMS and not params[key]]


def get_env_config(
    env_filepath: str = SKALE_DIR_ENV_FILEPATH, sync_node: bool = False
) -> Dict[str, str]:
    """Load and validate environment configuration from a file."""
    load_env_file(env_filepath)
    params = build_params(sync_node)
    populate_params(params)
    validate_params(params)
    return params


def load_env_file(env_filepath: str) -> None:
    """Check and load environment variables from the given file."""
    if not load_dotenv(dotenv_path=env_filepath):
        error_exit(f'Failed to load environment from {env_filepath}')


def build_params(sync_node: bool = False) -> Dict[str, str]:
    """Return a dictionary of parameters based on node type."""
    params = REQUIRED_PARAMS_SYNC.copy() if sync_node else REQUIRED_PARAMS.copy()
    params.update(OPTIONAL_PARAMS)
    return params


def populate_params(params: Dict[str, str]) -> None:
    """Populate params dictionary with environment variable values."""
    for key in params:
        env_value = os.getenv(key)
        if env_value is not None:
            params[key] = str(env_value)


def validate_params(params: Dict[str, str]) -> None:
    """Validate environment parameters."""
    missing = absent_params(params)
    if missing:
        error_exit(f'Missing required parameters: {missing}')
    validate_env_type(params['ENV_TYPE'])
    endpoint = params['ENDPOINT']
    validate_env_alias_or_address(params['IMA_CONTRACTS'], ContractType.IMA, endpoint)
    validate_env_alias_or_address(params['MANAGER_CONTRACTS'], ContractType.MANAGER, endpoint)


def validate_env_type(env_type: str) -> None:
    """Validate the environment type."""
    if env_type not in ALLOWED_ENV_TYPES:
        error_exit(f'Allowed ENV_TYPE values are {ALLOWED_ENV_TYPES}. Actual: "{env_type}"')


def validate_env_alias_or_address(
    alias_or_address: str, contract_type: ContractType, endpoint: str
) -> None:
    """Validate contract alias or address."""
    if is_contract_address(alias_or_address):
        validate_contract_address(alias_or_address, endpoint)
    else:
        validate_contract_alias(alias_or_address, contract_type, endpoint)


def validate_contract_address(contract_address: str, endpoint: str) -> None:
    """Validate if the given contract address has deployed code."""
    try:
        response = requests.post(
            endpoint,
            json={
                'jsonrpc': '2.0',
                'method': 'eth_getCode',
                'params': [contract_address, 'latest'],
                'id': 1,
            },
        )
        if response.status_code != 200:
            error_exit(f'Failed to verify contract at address {contract_address}')
        result = response.json().get('result')
        if not result or result in ['0x', '0x0']:
            error_exit(f'No contract code found at address {contract_address}')
    except requests.RequestException as e:
        error_exit(f'Failed to validate contract address: {str(e)}')


def get_deployment_url(alias: str, contract_type: ContractType, network_path: str) -> str:
    """Construct the deployment URL for the given contract alias and type."""
    return (
        f'https://raw.githubusercontent.com/skalenetwork/skale-contracts/'
        f'refs/heads/deployments/{network_path}/{contract_type.value}/{alias}.json'
    )


def validate_contract_alias(alias: str, contract_type: ContractType, endpoint: str) -> None:
    """Validate if the given contract alias exists in deployments for the current network."""
    try:
        chain_id = get_chain_id(endpoint)
        metadata = get_network_metadata()
        networks = metadata.get('networks', [])
        network_path: Optional[str] = None
        for net in networks:
            if net.get('chainId') == chain_id:
                network_path = net.get('path')
                break
        if not network_path:
            error_exit(f'Network with chain ID {chain_id} not found in metadata')
        assert isinstance(network_path, str)
        deployment_url = get_deployment_url(alias, contract_type, network_path)
        if requests.get(deployment_url).status_code != 200:
            error_exit(f"Contract alias '{alias}' not found for {contract_type.value}")
    except requests.RequestException as e:
        error_exit(f"Failed to validate contract alias '{alias}': {str(e)}")


def get_chain_id(endpoint: str) -> int:
    """Fetch chain ID from the JSON-RPC endpoint."""
    try:
        response = requests.post(
            endpoint,
            json={'jsonrpc': '2.0', 'method': 'eth_chainId', 'params': [], 'id': 1},
        )
        if response.status_code != 200:
            error_exit('Failed to get chain ID from endpoint')
        return int(response.json()['result'], 16)
    except requests.RequestException as e:
        error_exit(f'Failed to get chain ID: {str(e)}')
        # Will never reach this line, but needed for type checking.
        return 0


def get_network_metadata() -> Dict:
    """Fetch network metadata from GitHub."""
    try:
        response = requests.get(METADATA_URL)
        if response.status_code != 200:
            error_exit('Failed to fetch networks metadata')
        return response.json()
    except requests.RequestException as e:
        error_exit(f'Failed to fetch networks metadata: {str(e)}')
        # Will never reach this line, but needed for type checking.
        return {}


class NotValidEnvParamsError(Exception):
    """Raised when environment parameters are invalid or missing."""
