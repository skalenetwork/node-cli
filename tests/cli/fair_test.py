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

import mock
import requests
import logging

from node_cli.cli.fair import exit_node
from node_cli.configs import G_CONF_HOME

from tests.helper import response_mock, run_command_mock

logger = logging.getLogger(__name__)


def test_fair_node_exit():
    resp_mock = response_mock(requests.codes.ok, {'status': 'ok', 'payload': None})
    with mock.patch('node_cli.utils.decorators.is_node_inited', return_value=True):
        result = run_command_mock(
            'node_cli.utils.helper.requests.post',
            resp_mock,
            exit_node,
            ['--yes'],
        )
    assert result.exit_code == 0
    assert result.output == 'Removing node from fair manager contracts...\nNode successfully removed from fair manager contracts\n'


def test_fair_node_exit_with_error():
    resp_mock = response_mock(
        requests.codes.ok,
        {'status': 'error', 'payload': ['Fair manager error']},
    )
    with mock.patch('node_cli.utils.decorators.is_node_inited', return_value=True):
        result = run_command_mock(
            'node_cli.utils.helper.requests.post',
            resp_mock,
            exit_node,
            ['--yes'],
        )
    assert result.exit_code == 3
    assert 'Removing node from fair manager contracts...' in result.output
    assert 'Command failed with following errors:' in result.output
    assert 'Fair manager error' in result.output


def test_fair_node_exit_not_inited():
    resp_mock = response_mock(requests.codes.ok, {'status': 'ok', 'payload': None})
    result = run_command_mock(
        'node_cli.utils.helper.requests.post',
        resp_mock,
        exit_node,
        ['--yes'],
    )
    assert result.exit_code == 8
    assert "Node hasn't been inited before" in result.output