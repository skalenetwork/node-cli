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

import click
from terminaltables import SingleTable

from core.helper import login_required, get, safe_load_texts


TEXTS = safe_load_texts()


@click.group()
def sgx_cli():
    pass


@sgx_cli.group('sgx', help="SGX commands")
def sgx():
    pass


@sgx.command(help="Status of the SGX server")
@login_required
def status():
    result = get('sgx_status')
    if not result:
        return
    else:
        table_data = [
            ['SGX server URL', result['sgx_server_url']],
            ['Status', result['status_name']]
        ]
        table = SingleTable(table_data)
        print('SGX server status:')
        print(table.table)
