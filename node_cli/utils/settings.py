#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
#
#   Copyright (C) 2026 SKALE Labs
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

from skale.core.settings import (
    SETTINGS_MAP,
    write_node_settings_file,
    write_internal_settings_file,
    InternalSettings,
    SkaleSettings,
    SkalePassiveSettings,
    FairSettings,
    FairBaseSettings,
)

from node_cli.configs import NODE_SETTINGS_PATH, INTERNAL_SETTINGS_PATH

from node_cli.utils.node_type import NodeMode, NodeType

InternalSettings.model_config['toml_file'] = INTERNAL_SETTINGS_PATH
SkaleSettings.model_config['toml_file'] = NODE_SETTINGS_PATH
SkalePassiveSettings.model_config['toml_file'] = NODE_SETTINGS_PATH
FairSettings.model_config['toml_file'] = NODE_SETTINGS_PATH
FairBaseSettings.model_config['toml_file'] = NODE_SETTINGS_PATH


def save_settings(node_type: NodeType, node_mode: NodeMode) -> None:
    write_internal_settings_file(path=INTERNAL_SETTINGS_PATH, data={})  # todof: fix
    settings_type = SETTINGS_MAP[(node_type.value, node_mode.value)]
    write_node_settings_file(
        path=NODE_SETTINGS_PATH, settings_type=settings_type, data={}
    )  # todof: fix
