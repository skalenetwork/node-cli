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

import inspect
import os
from typing import Dict, NamedTuple
from dataclasses import dataclass
from abc import ABC

from dotenv.main import DotEnv

from node_cli.configs import SKALE_DIR, CONTAINER_CONFIG_PATH
from node_cli.configs.alias_address_validation import validate_alias_or_address, ContractType
from node_cli.utils.node_type import NodeType
from node_cli.utils.helper import error_exit

SKALE_DIR_ENV_FILEPATH = os.path.join(SKALE_DIR, '.env')
CONFIGS_ENV_FILEPATH = os.path.join(CONTAINER_CONFIG_PATH, '.env')

ALLOWED_ENV_TYPES = ['mainnet', 'testnet', 'qanet', 'devnet']


class ValidationResult(NamedTuple):
    result: bool
    missing: set
    extra: set


@dataclass(kw_only=True)
class BaseUserConfig(ABC):
    container_configs_stream: str
    env_type: str
    filebeat_host: str
    disk_mountpoint: str

    container_configs_dir: str = ''
    skip_docker_config: str = ''
    skip_docker_cleanup: str = ''

    def to_env(self) -> Dict[str, str]:
        result = {}
        for field_name, field_value in self.__dict__.items():
            upper_key = field_name.upper()
            result[upper_key] = str(field_value) if field_value is not None else ''
        return result

    @classmethod
    def validate_params(cls, params: Dict) -> ValidationResult:
        parameters = inspect.signature(cls.__init__).parameters
        missing = []
        keys = params.keys()
        expected_keys = {
            name.upper()
            for name, value in parameters.items()
            if name != 'self' and value.default == inspect._empty
        }
        optional_keys = {
            name.upper()
            for name, value in parameters.items()
            if name != 'self' and value.default != inspect._empty
        }
        missing = expected_keys - keys
        extra = keys - expected_keys - optional_keys
        return ValidationResult(missing == set() and extra == set(), missing, extra)


@dataclass
class MirageUserConfig(BaseUserConfig):
    mirage_contracts: str
    boot_endpoint: str
    sgx_server_url: str
    enforce_btrfs: str = ''


@dataclass
class MirageBootUserConfig(BaseUserConfig):
    endpoint: str
    manager_contracts: str
    ima_contracts: str
    sgx_server_url: str
    enforce_btrfs: str = ''


@dataclass
class SkaleUserConfig(BaseUserConfig):
    endpoint: str
    manager_contracts: str
    ima_contracts: str
    docker_lvmpy_stream: str
    sgx_server_url: str
    monitoring_containers: str = ''
    telegraf: str = ''
    influx_token: str = ''
    influx_url: str = ''
    tg_api_key: str = ''
    tg_chat_id: str = ''
    disable_dry_run: str = ''
    default_gas_limit: str = ''
    default_gas_price_wei: str = ''


@dataclass
class SyncUserConfig(BaseUserConfig):
    endpoint: str
    manager_contracts: str
    schain_name: str = ''
    ima_contracts: str = ''
    enforce_btrfs: str = ''


def get_validated_user_config(
    node_type: NodeType,
    env_filepath: str = SKALE_DIR_ENV_FILEPATH,
    is_mirage_boot: bool = False,
) -> BaseUserConfig:
    params = parse_env_file(env_filepath)
    user_config_type = get_user_config_type(node_type, is_mirage_boot)
    _, missing_params, extra_params = user_config_type.validate_params(params)

    if len(missing_params) > 0:
        error_exit(f'Missing required parameters: {missing_params}')

    if len(extra_params) > 0:
        error_exit(f'Extra parameters: {extra_params}')

    params = to_lower_keys(params)
    user_config = user_config_type(**params)
    validate_user_config(user_config)

    return user_config


def validate_user_config(user_config: BaseUserConfig) -> None:
    validate_env_type(env_type=user_config.env_type)

    if  isinstance(user_config, MirageUserConfig):
        contract_alias_or_address = user_config.mirage_contracts
    else:
        contract_alias_or_address = user_config.manager_contracts

    validate_alias_or_address(contract_alias_or_address, ContractType.MANAGER, user_config.endpoint)

    if isinstance(user_config, (SkaleUserConfig, MirageBootUserConfig)):
        validate_alias_or_address(user_config.ima_contracts, ContractType.IMA, user_config.endpoint)


def to_lower_keys(params: Dict[str, str]) -> Dict[str, str]:
    return {key.lower(): value for key, value in params.items()}


def parse_env_file(env_filepath: str) -> Dict:
    if not os.path.isfile(env_filepath):
        error_exit(f'Failed to load environment from {env_filepath}')
    return DotEnv(env_filepath).dict()


def get_user_config_type(
    node_type: NodeType,
    is_mirage_boot: bool = False,
) -> type[BaseUserConfig]:
    if node_type == NodeType.MIRAGE and is_mirage_boot:
        user_config_type = MirageBootUserConfig
    elif node_type == NodeType.MIRAGE:
        user_config_type = MirageUserConfig
    elif node_type == NodeType.SYNC:
        user_config_type = SyncUserConfig
    else:
        user_config_type = SkaleUserConfig
    return user_config_type


def validate_env_type(env_type: str) -> None:
    if env_type not in ALLOWED_ENV_TYPES:
        error_exit(f'Allowed ENV_TYPE values are {ALLOWED_ENV_TYPES}. Actual: "{env_type}"')
