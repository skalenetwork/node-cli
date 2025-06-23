#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
#
#   Copyright (C) 2025 SKALE Labs
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

import yaml

from node_cli.configs import (
    CONTAINER_CONFIG_PATH,
    MIRAGE_STATIC_PARAMS_FILEPATH,
    STATIC_PARAMS_FILEPATH,
)
from node_cli.utils.node_type import NodeType


def get_static_params(
    node_type: NodeType,
    env_type: str = 'mainnet',
    config_path: str = CONTAINER_CONFIG_PATH,
) -> dict:
    if node_type == NodeType.MIRAGE:
        static_params_base_filepath = MIRAGE_STATIC_PARAMS_FILEPATH
    else:
        static_params_base_filepath = STATIC_PARAMS_FILEPATH

    static_params_filename = os.path.basename(static_params_base_filepath)
    static_params_filepath = os.path.join(config_path, static_params_filename)
    with open(static_params_filepath) as requirements_file:
        ydata = yaml.load(requirements_file, Loader=yaml.Loader)
        return ydata['envs'][env_type]
