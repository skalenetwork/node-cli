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

import pytest

from node_cli.configs import NODE_SETTINGS_PATH
from node_cli.utils.node_type import NodeMode, NodeType
from node_cli.utils.settings import validate_and_save_node_settings


@pytest.mark.parametrize('endpoint', ['ws://localhost:8545', 'wss://localhost:8545'])
def test_validate_and_save_node_settings_non_http_endpoint(regular_user_conf, endpoint, capsys):
    regular_user_conf.write_text(
        regular_user_conf.read_text().replace('http://localhost:8545', endpoint)
    )
    node_settings = NODE_SETTINGS_PATH.read_bytes()
    with pytest.raises(SystemExit):
        validate_and_save_node_settings(
            regular_user_conf.as_posix(), NodeType.SKALE, NodeMode.ACTIVE
        )
    assert 'Endpoint must be an http or https URL' in capsys.readouterr().out
    assert NODE_SETTINGS_PATH.read_bytes() == node_settings
