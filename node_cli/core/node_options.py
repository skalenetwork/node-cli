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

from node_cli.utils.helper import read_json, write_json, init_file
from node_cli.configs.node_options import NODE_OPTIONS_FILEPATH

logger = logging.getLogger(__name__)


class NodeOptions:
    def __init__(
        self,
        filepath: str = NODE_OPTIONS_FILEPATH
    ):
        self.filepath = filepath
        init_file(filepath, {})

    def _get(self, field_name: str):
        config = read_json(self.filepath)
        return config.get(field_name)

    def _set(self, field_name: str, field_value) -> None:
        config = read_json(self.filepath)
        config[field_name] = field_value
        write_json(self.filepath, config)

    def all(self) -> dict:
        return read_json(self.filepath)
