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
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import time

import requests

from tests.helper import response_mock, run_command_mock
from cli.sgx import info

def test_sgx_status():
    payload = {
        'sgx_server_url': 'https://127.0.0.1:1026',
        'sgx_wallet_version': '1.50.1-stable.0',
        'sgx_keyname': 'test_keyname',
        'status_name': 'CONNECTED'
    }
    resp_mock = response_mock(
        requests.codes.ok,
        json_data={'payload': payload, 'status': 'ok'}
    )
    result = run_command_mock(
        'core.helper.requests.get', resp_mock, info)

    print(result.output)

    assert result.exit_code == 0
    assert result.output == '\x1b(0lqqqqqqqqqqqqqqqqqqqwqqqqqqqqqqqqqqqqqqqqqqqqk\x1b(B\n\x1b(0x\x1b(B SGX info          \x1b(0x\x1b(B                        \x1b(0x\x1b(B\n\x1b(0tqqqqqqqqqqqqqqqqqqqnqqqqqqqqqqqqqqqqqqqqqqqqu\x1b(B\n\x1b(0x\x1b(B Server URL        \x1b(0x\x1b(B https://127.0.0.1:1026 \x1b(0x\x1b(B\n\x1b(0x\x1b(B SGXWallet Version \x1b(0x\x1b(B 1.50.1-stable.0        \x1b(0x\x1b(B\n\x1b(0x\x1b(B Node SGX keyname  \x1b(0x\x1b(B test_keyname           \x1b(0x\x1b(B\n\x1b(0x\x1b(B Status            \x1b(0x\x1b(B CONNECTED              \x1b(0x\x1b(B\n\x1b(0mqqqqqqqqqqqqqqqqqqqvqqqqqqqqqqqqqqqqqqqqqqqqj\x1b(B\n'  # noqa
