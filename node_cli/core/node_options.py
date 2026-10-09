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
        return self._set('node_mode', node_mode.value)

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


def set_passive_node_options(
    archive: bool,
    indexer: bool,
) -> None:
    node_options = NodeOptions()
    node_options.node_mode = NodeMode.PASSIVE
    node_options.archive = archive or indexer
    node_options.catchup = archive or indexer
    node_options.historic_state = archive
    logger.info('Node options set for passive mode.')


class NodeModeMismatchError(Exception):
    pass


def upsert_node_mode(node_mode: NodeMode | None = None) -> NodeMode:
    node_options = NodeOptions()
    try:
        options_mode = node_options.node_mode
        if node_mode is not None and options_mode != node_mode:
            raise NodeModeMismatchError(
                f'Cannot change node mode from {options_mode} to {node_mode}'
            )
        return options_mode
    except ValueError:
        if node_mode is None:
            raise NodeModeMismatchError('Node mode is not set')
        node_options.node_mode = node_mode
        return node_mode


def active_skale(node_type: NodeType, node_mode: NodeMode) -> bool:
    return node_mode == NodeMode.ACTIVE and node_type == NodeType.SKALE


def active_fair(node_type: NodeType, node_mode: NodeMode) -> bool:
    return node_mode == NodeMode.ACTIVE and node_type == NodeType.FAIR


def passive_skale(node_type: NodeType, node_mode: NodeMode) -> bool:
    return node_mode == NodeMode.PASSIVE and node_type == NodeType.SKALE


def passive_fair(node_type: NodeType, node_mode: NodeMode) -> bool:
    return node_mode == NodeMode.PASSIVE and node_type == NodeType.FAIR
