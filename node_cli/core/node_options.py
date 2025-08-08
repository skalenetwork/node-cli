#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
#
#   Copyright (C) 2022 SKALE Labs
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

from node_cli.utils.node_type import NodeMode, NodeType
from node_cli.utils.helper import read_json, write_json, init_file
from node_cli.configs.node_options import NODE_OPTIONS_FILEPATH
from node_cli.cli.info import TYPE


logger = logging.getLogger(__name__)


class NodeOptions:
    def __init__(self, filepath: str = NODE_OPTIONS_FILEPATH):
        self.filepath = filepath
        init_file(filepath, {})

    def _get(self, field_name: str):
        config = read_json(self.filepath)
        return config.get(field_name)

    def _set(self, field_name: str, field_value) -> None:
        config = read_json(self.filepath)
        config[field_name] = field_value
        write_json(self.filepath, config)

    @property
    def archive(self) -> bool:
        return self._get('archive') or False

    @archive.setter
    def archive(self, archive: bool) -> None:
        return self._set('archive', archive)

    @property
    def catchup(self) -> bool:
        return self._get('catchup') or False

    @catchup.setter
    def catchup(self, catchup: bool) -> None:
        return self._set('catchup', catchup)

    @property
    def historic_state(self) -> bool:
        return self._get('historic_state') or False

    @historic_state.setter
    def historic_state(self, historic_state: bool) -> None:
        return self._set('historic_state', historic_state)

    @property
    def node_mode(self) -> NodeMode:
        return NodeMode(self._get('node_mode'))

    @node_mode.setter
    def node_mode(self, node_mode: NodeMode) -> None:
        return self._set('node_mode', node_mode.name)

    def all(self) -> dict:
        return read_json(self.filepath)


def mark_active_node() -> None:
    node_options = NodeOptions()
    node_options.node_mode = NodeMode.ACTIVE
    logger.info('Node marked as active.')


def mark_passive_node() -> None:
    node_options = NodeOptions()
    node_options.node_mode = NodeMode.PASSIVE
    logger.info('Node marked as passive.')


def is_active_node() -> bool:
    node_options = NodeOptions()
    return node_options.node_mode == NodeMode.ACTIVE


def is_passive_node() -> bool:
    node_options = NodeOptions()
    return node_options.node_mode == NodeMode.PASSIVE


def is_skale_node() -> bool:
    return TYPE == NodeType.SKALE


def is_fair_node() -> bool:
    return TYPE == NodeType.FAIR
