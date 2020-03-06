#   -*- coding: utf-8 -*-
#
#   This file is part of skale-node-cli
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

from cli.wallet import wallet_info
from tests.helper import run_command_mock


def test_wallet_info(config):
    response_data = {
        'data': {
            'address': 'simple_address',
            'eth_balance': 13,
            'skale_balance': 123
        }
    }
    response_mock = MagicMock()
    response_mock.status_code = requests.codes.ok
    response_mock.json = Mock(return_value=response_data)
    result = run_command_mock('core.wallet.get_request',
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

    result = run_command_mock('core.wallet.get_request',
                              response_mock,
                              wallet_info,
                              ['--format', 'json'])
    assert result.exit_code == 0
    expected = (
        "{\"address\": \"simple_address\", "
        "\"eth_balance\": 13, \"skale_balance\": 123}\n"
    )
    assert result.output == expected
