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

import tomllib
from pathlib import Path

from dotenv.main import DotEnv

from skale_core.settings import (
    SETTINGS_MAP,
    BaseNodeSettings,
    FairBaseSettings,
    FairSettings,
    InternalSettings,
    SkalePassiveSettings,
    SkaleSettings,
    write_internal_settings_file,
    write_node_settings_file,
)

from node_cli.configs import INTERNAL_SETTINGS_PATH, NODE_SETTINGS_PATH, SKALE_DIR
from node_cli.utils.node_type import NodeMode, NodeType

InternalSettings.model_config['toml_file'] = INTERNAL_SETTINGS_PATH
SkaleSettings.model_config['toml_file'] = NODE_SETTINGS_PATH
SkalePassiveSettings.model_config['toml_file'] = NODE_SETTINGS_PATH
FairSettings.model_config['toml_file'] = NODE_SETTINGS_PATH
FairBaseSettings.model_config['toml_file'] = NODE_SETTINGS_PATH


def load_config_file(filepath: str) -> dict:
    if filepath.endswith('.toml'):
        with open(filepath, 'rb') as f:
            return tomllib.load(f)
    return {k.lower(): v for k, v in DotEnv(filepath).dict().items()}


def _remove_if_exists(path: Path) -> None:
    if path.exists():
        path.unlink()


def validate_and_save_node_settings(
    config_filepath: str,
    node_type: NodeType,
    node_mode: NodeMode,
) -> BaseNodeSettings:
    data = load_config_file(config_filepath)
    settings_type = SETTINGS_MAP[(node_type.value, node_mode.value)]
    settings_type.model_validate(data)
    _remove_if_exists(NODE_SETTINGS_PATH)
    write_node_settings_file(path=NODE_SETTINGS_PATH, settings_type=settings_type, data=data)
    return settings_type()


def save_internal_settings(
    node_type: NodeType,
    node_mode: NodeMode,
    backup_run: bool = False,
    pull_config_for_schain: str | None = None,
) -> None:
    data = {
        'node_type': node_type.value,
        'node_mode': node_mode.value,
        'skale_dir_host': str(SKALE_DIR),
        'backup_run': backup_run,
        'pull_config_for_schain': pull_config_for_schain,
    }
    InternalSettings.model_validate(data)
    _remove_if_exists(INTERNAL_SETTINGS_PATH)
    write_internal_settings_file(path=INTERNAL_SETTINGS_PATH, data=data)
