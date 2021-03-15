#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
#
#   Copyright (C) 2021 SKALE Labs
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

import yaml
from node_cli.utils.helper import safe_load_yml
from node_cli.configs import NET_PARAMS_FILEPATH


def read_node_params():
    return safe_load_yml(NET_PARAMS_FILEPATH)


def get_config_env_section(env_type: str, section: str):
    configs = read_node_params()
    return configs[env_type][section]


def get_config_env_schain_option(env_type: str, key: str):
    return get_config_env_section(env_type, 'schain')[key]


def get_net_params(network: str = 'mainnet'):
    with open(NET_PARAMS_FILEPATH) as requirements_file:
        ydata = yaml.load(requirements_file, Loader=yaml.Loader)
        return ydata[network]
