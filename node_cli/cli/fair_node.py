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
from node_cli.fair.fair_node import change_ip as change_ip_fair
from node_cli.fair.fair_node import cleanup as fair_cleanup
from node_cli.fair.fair_node import exit as exit_fair
from node_cli.fair.fair_node import (
    get_node_info,
    migrate_from_boot,
    repair_chain,
    restore_fair,
)
from node_cli.fair.fair_node import init as init_fair
from node_cli.fair.fair_node import register as register_fair
from node_cli.fair.fair_node import update as update_fair
from node_cli.utils.helper import IP_TYPE, URL_OR_ANY_TYPE, abort_if_false, streamed_cmd
from node_cli.utils.texts import safe_load_texts

TEXTS = safe_load_texts()


@click.group()
def fair_node_cli():
    pass


@fair_node_cli.group(help='Commands for regular Fair Node operations.')
def node():
    pass


@node.command('info', help='Get info about Fair node.')
@click.option('--format', '-f', type=click.Choice(['json', 'text']))
def fair_node_info(format):
    get_node_info(format)


@node.command('init', help='Initialize regular Fair node')
@click.argument('env_filepath')
@streamed_cmd
def init_node(env_filepath: str):
    init_fair(env_filepath=env_filepath)


@node.command('register', help=TEXTS['fair']['node']['register']['help'])
@click.option('--ip', required=True, type=IP_TYPE, help=TEXTS['fair']['node']['register']['ip'])
def register(ip: str) -> None:
    register_fair(ip=ip)


@node.command('update', help='Update Fair node')
@click.argument('env_filepath')
@click.option(
    '--yes',
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt='Are you sure you want to update Fair node software?',
)
@click.option('--pull-config', 'pull_config_for_schain', hidden=True, type=str)
@click.option(
    '--force-skaled-start',
    'force_skaled_start',
    hidden=True,
    type=bool,
    default=False,
    is_flag=True,
)
@streamed_cmd
def update_node(env_filepath: str, pull_config_for_schain, force_skaled_start: bool):
    update_fair(
        env_filepath=env_filepath,
        pull_config_for_schain=pull_config_for_schain,
        force_skaled_start=force_skaled_start,
    )


@node.command('backup', help='Generate backup file for the Fair node.')
@click.argument('backup_folder_path')
@streamed_cmd
def backup_node(backup_folder_path):
    backup(backup_folder_path)


@node.command('restore', help='Restore Fair node from a backup file.')
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
    restore_fair(backup_path, env_file, config_only)


@node.command('migrate', help='Switch from boot to regular Fair node.')
@click.argument('env_filepath')
@click.option(
    '--yes',
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt='Are you sure you want to migrate to regular Fair node? The action cannot be undone',
)
@streamed_cmd
def migrate_node(env_filepath: str) -> None:
    migrate_from_boot(env_filepath=env_filepath)


@node.command('repair', help='Toggle fair chain repair mode')
@click.option(
    '--snapshot-from',
    type=URL_OR_ANY_TYPE,
    default='any',
    hidden=True,
    help=TEXTS['fair']['node']['repair']['snapshot_from'],
)
@click.option(
    '--yes',
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt=TEXTS['fair']['node']['repair']['warning'],
)
@streamed_cmd
def repair(snapshot_from: str = 'any') -> None:
    repair_chain(snapshot_from=snapshot_from)


@node.command('cleanup', help='Cleanup Fair node.')
@click.option(
    '--yes',
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt='Are you sure you want to cleanup Fair node?',
)
@streamed_cmd
def cleanup_node():
    fair_cleanup()


@node.command('change-ip', help=TEXTS['fair']['node']['change-ip']['help'])
@click.argument('ip', type=IP_TYPE)
def change_ip(ip: str) -> None:
    change_ip_fair(ip=ip)


@node.command('exit', help=TEXTS['fair']['node']['exit']['help'])
@click.option(
    '--yes',
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt=TEXTS['fair']['node']['exit']['prompt'],
)
def exit_node() -> None:
    exit_fair()
