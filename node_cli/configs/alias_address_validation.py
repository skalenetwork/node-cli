#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
#
#   Copyright (C) 2025-Present SKALE Labs
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

from enum import Enum
from typing import Dict, Optional

import requests

from node_cli.utils.helper import error_exit, is_contract_address


METADATA_URL: str = (
    'https://raw.githubusercontent.com/skalenetwork/skale-contracts/'
    'refs/heads/deployments/metadata.json'
)


class ContractType(Enum):
    """Contract types supported by the system using skale-contracts library."""

    IMA = 'mainnet-ima'
    MANAGER = 'skale-manager'


def validate_env_alias_or_address(
    alias_or_address: str, contract_type: ContractType, endpoint: str
) -> None:
    if is_contract_address(alias_or_address):
        validate_contract_address(alias_or_address, endpoint)
    else:
        validate_contract_alias(alias_or_address, contract_type, endpoint)


def validate_contract_address(contract_address: str, endpoint: str) -> None:
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
    return (
        f'https://raw.githubusercontent.com/skalenetwork/skale-contracts/'
        f'refs/heads/deployments/{network_path}/{contract_type.value}/{alias}.json'
    )


def validate_contract_alias(alias: str, contract_type: ContractType, endpoint: str) -> None:
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
        if not isinstance(network_path, str):
            error_exit(f'Invalid network path type: {network_path}')
        deployment_url = get_deployment_url(alias, contract_type, network_path)
        if requests.get(deployment_url).status_code != 200:
            error_exit(f"Contract alias '{alias}' not found for {contract_type.value}")
    except requests.RequestException as e:
        error_exit(f"Failed to validate contract alias '{alias}': {str(e)}")


def get_chain_id(endpoint: str) -> int:
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


def get_network_metadata() -> Dict:
    try:
        response = requests.get(METADATA_URL)
        if response.status_code != 200:
            error_exit('Failed to fetch networks metadata')
        return response.json()
    except requests.RequestException as e:
        error_exit(f'Failed to fetch networks metadata: {str(e)}')
