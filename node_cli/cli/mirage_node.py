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

from node_cli.core.node import backup
from node_cli.mirage.mirage_node import cleanup as mirage_cleanup
from node_cli.mirage.mirage_node import init as init_mirage
from node_cli.mirage.mirage_node import (
    migrate_from_boot,
    request_repair,
    restore_mirage,
    get_node_info,
)
from node_cli.mirage.mirage_node import register as register_mirage
from node_cli.mirage.mirage_node import update as update_mirage
from node_cli.utils.helper import IP_TYPE, URL_TYPE, abort_if_false, streamed_cmd
from node_cli.utils.texts import safe_load_texts

TEXTS = safe_load_texts()


@click.group()
def mirage_node_cli():
    pass


@mirage_node_cli.group(help='Commands for regular Mirage Node operations.')
def node():
    pass


@node.command('info', help='Get info about Mirage node.')
@click.option('--format', '-f', type=click.Choice(['json', 'text']))
def mirage_node_info(format):
    get_node_info(format)


@node.command('init', help='Initialize regular Mirage node')
@click.argument('env_filepath')
@streamed_cmd
def init_node(env_filepath: str):
    init_mirage(env_filepath=env_filepath)


@node.command('register', help=TEXTS['mirage']['node']['register']['help'])
@click.option('--ip', required=True, type=IP_TYPE, help=TEXTS['mirage']['node']['register']['ip'])
def register(ip: str) -> None:
    register_mirage(ip=ip)


@node.command('update', help='Update Mirage node')
@click.argument('env_filepath')
@click.option(
    '--yes',
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt='Are you sure you want to update Mirage node software?',
)
@click.option('--pull-config', 'pull_config_for_schain', hidden=True, type=str)
@streamed_cmd
def update_node(env_filepath: str, pull_config_for_schain):
    update_mirage(env_filepath=env_filepath, pull_config_for_schain=pull_config_for_schain)


@node.command('backup', help='Generate backup file for the Mirage node.')
@click.argument('backup_folder_path')
@streamed_cmd
def backup_node(backup_folder_path):
    backup(backup_folder_path)


@node.command('restore', help='Restore Mirage node from a backup file.')
@click.argument('backup_path')
@click.argument('env_file')
@click.option(
    '--config-only',
    help='Only restore configuration files in .skale and artifacts',
    is_flag=True,
    hidden=True,
)
@streamed_cmd
def restore_node(backup_path, env_file, config_only):
    restore_mirage(backup_path, env_file, config_only)


@node.command('migrate', help='Switch from boot to regular Mirage node.')
@click.argument('env_filepath')
@click.option(
    '--yes',
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt='Are you sure you want to migrate to regular Mirage node? The action cannot be undone',
)
@streamed_cmd
def migrate_node(env_filepath: str) -> None:
    migrate_from_boot(env_filepath=env_filepath)


@node.command('repair', help='Toggle mirage chain repair mode')
@click.option(
    '--snapshot-from',
    type=URL_TYPE,
    default='',
    hidden=True,
    help=TEXTS['mirage']['node']['repair']['snapshot_from'],
)
@click.option(
    '--yes',
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt=TEXTS['mirage']['node']['repair']['warning'],
)
def repair(snapshot_from: str = '') -> None:
    request_repair(snapshot_from=snapshot_from)


@node.command('cleanup', help='Cleanup Mirage node.')
@click.option(
    '--yes',
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt='Are you sure you want to cleanup Mirage node?',
)
@streamed_cmd
def cleanup_node():
    mirage_cleanup()
