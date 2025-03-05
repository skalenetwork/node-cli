"""Environment configuration and validation module for SKALE node.

This module handles environment variable loading, validation, and configuration
for SKALE node setup. It ensures all required parameters are present and valid.
"""

import os
from typing import Dict, List, Optional
from dotenv import load_dotenv
import requests
from enum import Enum

from node_cli.configs import SKALE_DIR, CONTAINER_CONFIG_PATH
from node_cli.utils.helper import error_exit
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
    'MANAGER_CONTRACTS_ALIAS_OR_ADDRESS': '',
    'IMA_CONTRACTS_ALIAS_OR_ADDRESS': '',
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
    'MANAGER_CONTRACTS_ALIAS_OR_ADDRESS': '',
    'IMA_CONTRACTS_ALIAS_OR_ADDRESS': '',
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
    if not os.path.exists(env_filepath):
        error_exit(f'Environment file not found: {env_filepath}', CLIExitCodes.FAILURE)
    if not os.access(env_filepath, os.R_OK):
        error_exit(f'Cannot read environment file: {env_filepath}', CLIExitCodes.FAILURE)
    if not load_dotenv(dotenv_path=env_filepath):
        error_exit(f'Failed to load environment from {env_filepath}', CLIExitCodes.FAILURE)


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
        error_exit(f'Missing required parameters: {missing}', CLIExitCodes.FAILURE)
    validate_env_type(params['ENV_TYPE'])
    # Get the endpoint explicitly from the params.
    endpoint = params['ENDPOINT']
    validate_env_alias_or_address(
        params['IMA_CONTRACTS_ALIAS_OR_ADDRESS'], ContractType.IMA, endpoint
    )
    validate_env_alias_or_address(
        params['MANAGER_CONTRACTS_ALIAS_OR_ADDRESS'], ContractType.MANAGER, endpoint
    )


def validate_env_type(env_type: str) -> None:
    """Validate the environment type."""
    if env_type not in ALLOWED_ENV_TYPES:
        error_exit(
            f'Allowed ENV_TYPE values are {ALLOWED_ENV_TYPES}. Actual: "{env_type}"',
            CLIExitCodes.FAILURE,
        )


def validate_env_alias_or_address(
    alias_or_address: str, contract_type: ContractType, endpoint: str
) -> None:
    """Validate contract alias or address."""
    if not alias_or_address:
        param_name = (
            'IMA_CONTRACTS_ALIAS_OR_ADDRESS'
            if contract_type == ContractType.IMA
            else 'MANAGER_CONTRACTS_ALIAS_OR_ADDRESS'
        )
        error_exit(f'{param_name} is not set', CLIExitCodes.FAILURE)
    # If alias_or_address is 42 characters and starts with '0x', treat it as a contract address.
    # TODO: Add a more robust check for contract address and see if doesn't conflict with alias.
    if len(alias_or_address) == 42 and alias_or_address.startswith('0x'):
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
            error_exit(
                f'Failed to verify contract at address {contract_address}', CLIExitCodes.FAILURE
            )
        result = response.json().get('result')
        if not result or result in ['0x', '0x0']:
            error_exit(
                f'No contract code found at address {contract_address}', CLIExitCodes.FAILURE
            )
    except requests.RequestException as e:
        error_exit(f'Failed to validate contract address: {str(e)}', CLIExitCodes.FAILURE)


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
            error_exit(
                f'Network with chain ID {chain_id} not found in metadata', CLIExitCodes.FAILURE
            )
        deployment_url = (
            f'https://raw.githubusercontent.com/skalenetwork/skale-contracts/'
            f'refs/heads/deployments/{network_path}/{contract_type.value}/{alias}.json'
        )
        if requests.get(deployment_url).status_code != 200:
            error_exit(
                f"Contract alias '{alias}' not found for {contract_type.value}",
                CLIExitCodes.FAILURE,
            )
    except requests.RequestException as e:
        error_exit(f"Failed to validate contract alias '{alias}': {str(e)}", CLIExitCodes.FAILURE)


def get_chain_id(endpoint: str) -> int:
    """Fetch chain ID from the JSON-RPC endpoint."""
    try:
        response = requests.post(
            endpoint,
            json={'jsonrpc': '2.0', 'method': 'eth_chainId', 'params': [], 'id': 1},
        )
        if response.status_code != 200:
            error_exit('Failed to get chain ID from endpoint', CLIExitCodes.FAILURE)
        return int(response.json()['result'], 16)
    except requests.RequestException as e:
        error_exit(f'Failed to get chain ID: {str(e)}', CLIExitCodes.FAILURE)
        # Will never reach this line, but needed for type checking.
        return 0


def get_network_metadata() -> Dict:
    """Fetch network metadata from GitHub."""
    metadata_url = (
        'https://raw.githubusercontent.com/skalenetwork/skale-contracts/'
        'refs/heads/deployments/metadata.json'
    )
    try:
        response = requests.get(metadata_url)
        if response.status_code != 200:
            error_exit('Failed to fetch networks metadata', CLIExitCodes.FAILURE)
        return response.json()
    except requests.RequestException as e:
        error_exit(f'Failed to fetch networks metadata: {str(e)}', CLIExitCodes.FAILURE)
        # Will never reach this line, but needed for type checking.
        return {}


class NotValidEnvParamsError(Exception):
    """Raised when environment parameters are invalid or missing."""
