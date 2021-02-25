#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
#
#   Copyright (C) 2019 SKALE Labs
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.


import requests

from mock import MagicMock, Mock

from node_cli.cli.wallet import wallet_info, send
from tests.helper import run_command_mock, response_mock


def test_wallet_info():
    response_data = {
        'status': 'ok',
        'payload': {
            'address': 'simple_address',
            'eth_balance': 13,
            'skale_balance': 123
        }
    }
    response_mock = MagicMock()
    response_mock.status_code = requests.codes.ok
    response_mock.json = Mock(return_value=response_data)
    result = run_command_mock('node_cli.utils.helper.requests.get',
                              response_mock,
                              wallet_info)
    assert result.exit_code == 0
    expected = (
        '--------------------------------------------------\n'
        'Address: simple_address\n'
        'ETH balance: 13 ETH\n'
        'SKALE balance: 123 SKALE\n'
        '--------------------------------------------------\n'
    )
    assert result.output == expected

    result = run_command_mock('node_cli.utils.helper.requests.get',
                              response_mock,
                              wallet_info,
                              ['--format', 'json'])
    assert result.exit_code == 0
    expected = (
        "{\"address\": \"simple_address\", "
        "\"eth_balance\": 13, \"skale_balance\": 123}\n"
    )
    assert result.output == expected


def test_wallet_send():
    resp_mock = response_mock(
        requests.codes.ok,
        {'status': 'ok', 'payload': None}
    )
    result = run_command_mock(
        'node_cli.utils.helper.requests.post',
        resp_mock,
        send,
        ['0x00000000000000000000000000000000', '10', '--yes'])
    assert result.exit_code == 0
    assert result.output == 'Funds were successfully transferred\n'  # noqa


def test_wallet_send_with_error():
    resp_mock = response_mock(
        requests.codes.ok,
        {'status': 'error', 'payload': ['Strange error']},
    )
    result = run_command_mock(
        'node_cli.utils.helper.requests.post',
        resp_mock,
        send,
        ['0x00000000000000000000000000000000', '10', '--yes'])
    assert result.exit_code == 3
    assert result.output == 'Command failed with following errors:\n--------------------------------------------------\nStrange error\n--------------------------------------------------\nYou can find more info in tests/.skale/.skale-cli-log/debug-node-cli.log\n'  # noqa
