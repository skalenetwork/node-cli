#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
#
#   Copyright (C) 2022 SKALE Labs
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

from typing import Optional

import click

from node_cli.core.node import init_sync, update_sync, repair_sync
from node_cli.utils.helper import (
    abort_if_false,
    error_exit,
    safe_load_texts,
    streamed_cmd,
    URL_TYPE
)
from node_cli.utils.exit_codes import CLIExitCodes


G_TEXTS = safe_load_texts()
TEXTS = G_TEXTS['sync_node']


@click.group()
def sync_node_cli():
    pass


@sync_node_cli.group(help="SKALE sync node commands")
def sync_node():
    pass


@sync_node.command('init', help=TEXTS['init']['help'])
@click.argument('env_file')
@click.option(
    '--archive',
    help=TEXTS['init']['archive'],
    is_flag=True
)
@click.option(
    '--catchup',
    help=TEXTS['init']['catchup'],
    is_flag=True
)
@click.option(
    '--historic-state',
    help=TEXTS['init']['historic_state'],
    is_flag=True
)
@click.option(
    '--snapshot-from',
    type=URL_TYPE,
    default=None,
    hidden=True,
    help='Ip of the node from to download snapshot from'
)
@streamed_cmd
def _init_sync(env_file, archive, catchup, historic_state, snapshot_from: Optional[str]):
    if historic_state and not archive:
        error_exit(
            '--historic-state can be used only is combination with --archive',
            exit_code=CLIExitCodes.FAILURE
        )
    init_sync(env_file, archive, catchup, historic_state, snapshot_from)


@sync_node.command('update', help='Update sync node from .env file')
@click.option('--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              prompt='Are you sure you want to update SKALE node software?')
@click.option(
    '--unsafe',
    'unsafe_ok',
    help='Allow unsafe update',
    hidden=True,
    is_flag=True
)
@click.argument('env_file')
@streamed_cmd
def _update_sync(env_file, unsafe_ok):
    update_sync(env_file)


@sync_node.command('repair', help='Start sync node from empty database')
@click.option('--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              prompt='Are you sure you want to start sync node from empty database?')
@click.option(
    '--archive',
    help=TEXTS['init']['archive'],
    is_flag=True
)
@click.option(
    '--catchup',
    help=TEXTS['init']['catchup'],
    is_flag=True
)
@click.option(
    '--historic-state',
    help=TEXTS['init']['historic_state'],
    is_flag=True
)
@click.option(
    '--snapshot-from',
    type=URL_TYPE,
    default=None,
    hidden=True,
    help='Ip of the node from to download snapshot from'
)
@streamed_cmd
def _repair_sync(
    archive: str,
    catchup: str,
    historic_state: str,
    snapshot_from: Optional[str] = None
) -> None:
    repair_sync(
        archive=archive,
        catchup=catchup,
        historic_state=historic_state,
        snapshot_from=snapshot_from
    )
