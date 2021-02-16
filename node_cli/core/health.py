#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
#
#   Copyright (C) 2020 SKALE Labs
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

import json
from terminaltables import SingleTable

from node_cli.core.print_formatters import (
    print_containers,
    print_schains_healthchecks
)
from node_cli.utils.helper import error_exit, get_request
from node_cli.utils.exit_codes import CLIExitCodes


BLUEPRINT_NAME = 'health'


def get_containers(_all):
    status, payload = get_request(
        blueprint=BLUEPRINT_NAME,
        method='containers',
        params={'all': _all}
    )
    if status == 'ok':
        print_containers(payload)
    else:
        error_exit(payload, exit_code=CLIExitCodes.BAD_API_RESPONSE)


def get_schains_checks(json_format: bool = False) -> None:
    status, payload = get_request(
        blueprint=BLUEPRINT_NAME,
        method='schains'
    )
    if status == 'ok':
        if not payload:
            print('No sChains found')
            return
        if json_format:
            print(json.dumps(payload))
        else:
            print_schains_healthchecks(payload)
    else:
        error_exit(payload, exit_code=CLIExitCodes.BAD_API_RESPONSE)


def get_sgx_info():
    status, payload = get_request(
        blueprint=BLUEPRINT_NAME,
        method='sgx'
    )
    if status == 'ok':
        data = payload
        table_data = [
            ['SGX info', ''],
            ['Server URL', data['sgx_server_url']],
            ['SGXWallet Version', data['sgx_wallet_version']],
            ['Node SGX keyname', data['sgx_keyname']],
            ['Status', data['status_name']]
        ]
        table = SingleTable(table_data)
        print(table.table)
    else:
        error_exit(payload, exit_code=CLIExitCodes.BAD_API_RESPONSE)
