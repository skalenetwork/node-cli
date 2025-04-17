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

from node_cli.core.node import get_node_signature, backup
from node_cli.core.mirage_node import restore_mirage
from node_cli.utils.helper import error_exit, streamed_cmd
from node_cli.utils.decorators import check_inited


@click.group('node', help='Commands for regular Mirage Node operations.')
def mirage_node_cli():
    pass


@mirage_node_cli.command('init', help='Initialize regular Mirage node operations (Placeholder).')
@check_inited
def init_node():
    click.echo("Placeholder: Command 'mirage node init' is not yet implemented.")
    pass


@mirage_node_cli.command(
    'register', help='Register Mirage node (Placeholder for regular operations).'
)
@check_inited
def register_node():
    click.echo("Placeholder: Command 'mirage node register' is not yet implemented.")
    pass


@mirage_node_cli.command('signature', help='Get mirage node signature for a validator ID.')
@click.argument('validator_id')
def signature_node(validator_id):
    res = get_node_signature(validator_id)
    if isinstance(res, dict) and 'error' in res:
        error_exit(f'Error getting signature: {res.get("message", res)}')
    print(f'Signature: {res}')


@mirage_node_cli.command('backup', help='Generate backup file for the Mirage node.')
@click.argument('backup_folder_path')
@streamed_cmd
def backup_node(backup_folder_path):
    backup(backup_folder_path)


@mirage_node_cli.command('restore', help='Restore Mirage node from a backup file.')
@click.argument('backup_path')
@click.argument('env_file')
@click.option(
    '--no-snapshot', help='Do not restore mirage from snapshot', is_flag=True, hidden=True
)
@click.option(
    '--config-only',
    help='Only restore configuration files in .skale and artifacts',
    is_flag=True,
    hidden=True,
)
@streamed_cmd
def restore_node(backup_path, env_file, no_snapshot, config_only):
    restore_mirage(backup_path, env_file, no_snapshot, config_only)
