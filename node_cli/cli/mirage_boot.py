#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
#
#   Copyright (C) 2025-Present SKALE Labs
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

import click

from node_cli.core.node import get_node_signature, register_node as register
from node_cli.core.mirage_boot import init, migrate
from node_cli.configs import DEFAULT_NODE_BASE_PORT
from node_cli.utils.helper import streamed_cmd, IP_TYPE, error_exit, abort_if_false


@click.group('boot', help='Commands for the Mirage Boot phase.')
def mirage_boot_cli():
    pass


@mirage_boot_cli.command('init', help='Initialize Mirage node (Boot Phase).')
@click.argument('env_file')
@streamed_cmd
def init_boot(env_file):
    init(env_file)


@mirage_boot_cli.command(
    'register', help='Register Mirage node in SKALE Manager (during Boot Phase).'
)
@click.option(
    '--name', '-n', required=True, prompt='Enter mirage node name', help='Mirage node name'
)
@click.option(
    '--ip',
    prompt='Enter node public IP',
    type=IP_TYPE,
    help='Public IP for RPC connections & consensus (required)',
)
@click.option(
    '--port', '-p', default=DEFAULT_NODE_BASE_PORT, type=int, help='Base port for node sChains'
)
@click.option('--domain', '-d', prompt='Enter node domain name', type=str, help='Node domain name')
@streamed_cmd
def register_boot(name, ip, port, domain):
    register(name=name, p2p_ip=ip, public_ip=ip, port=port, domain_name=domain)


@mirage_boot_cli.command(
    'signature', help='Get mirage node signature for a validator ID (during Boot Phase).'
)
@click.argument('validator_id')
def signature_boot(validator_id):
    res = get_node_signature(validator_id)
    if isinstance(res, dict) and 'error' in res:
        error_exit(f'Error getting signature: {res.get("message", res)}')
    print(f'Signature: {res}')


@mirage_boot_cli.command(
    'migrate', help='Migrate mirage node from Mirage Boot Phase to Mirage Main Phase.'
)
@click.option(
    '--yes',
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt='Are you sure you want to mirage node from Mirage Boot Phase to Mirage Main Phase?',
)
@click.option('--pull-config', 'pull_config_for_schain', hidden=True, type=str)
@click.argument('env_file')
@streamed_cmd
def migrate_boot(env_file, pull_config_for_schain):
    migrate(env_file, pull_config_for_schain)
