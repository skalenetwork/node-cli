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

from node_cli.cli.fair import fair_node_exit_cmd

from tests.helper import response_mock, run_command_mock


def test_fair_node_exit():
    resp_mock = response_mock(requests.codes.ok, {'status': 'ok', 'payload': None})

    with mock.patch('node_cli.utils.decorators.is_node_inited', return_value=True):
        result = run_command_mock(
            'node_cli.utils.helper.requests.post',
            resp_mock,
            fair_node_exit_cmd,
            ['--yes'],
        )
    assert result.exit_code == 0
    assert (
        result.output == 'Removing node from fair manager contracts...\nNode successfully removed from fair manager contracts\n'
    )


def test_fair_node_exit_fail():
    resp_mock = response_mock(requests.codes.bad_request, {'status': 'error', 'payload': 'Failed to remove node'})

    with mock.patch('node_cli.utils.decorators.is_node_inited', return_value=True):
        result = run_command_mock(
            'node_cli.utils.helper.requests.post',
            resp_mock,
            fair_node_exit_cmd,
            ['--yes'],
        )
    assert result.exit_code == 4