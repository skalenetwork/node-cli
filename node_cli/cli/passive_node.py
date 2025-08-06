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

from node_cli.core.node import init_passive, update_passive, cleanup_passive
from node_cli.utils.helper import (
    abort_if_false,
    error_exit,
    streamed_cmd,
    URL_TYPE,
)
from node_cli.utils.texts import safe_load_texts


G_TEXTS = safe_load_texts()
TEXTS = G_TEXTS['passive_node']


@click.group()
def passive_node_cli():
    pass


@passive_node_cli.group(help='SKALE passive node commands')
def passive_node():
    pass


@passive_node.command('init', help=TEXTS['init']['help'])
@click.argument('env_file')
@click.option('--indexer', help=TEXTS['init']['indexer'], is_flag=True)
@click.option('--archive', help=TEXTS['init']['archive'], is_flag=True)
@click.option('--snapshot', help=TEXTS['init']['snapshot'], is_flag=True)
@click.option(
    '--snapshot-from', type=URL_TYPE, default=None, hidden=True, help=TEXTS['init']['snapshot_from']
)
@streamed_cmd
def _init_passive(
    env_file, indexer: bool, archive: bool, snapshot: bool, snapshot_from: Optional[str]
) -> None:
    if indexer and archive:
        error_exit('Cannot use both --indexer and --archive options')
    init_passive(env_file, indexer, archive, snapshot, snapshot_from)


@passive_node.command('update', help='Update passive node from .env file')
@click.option(
    '--yes',
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt='Are you sure you want to update SKALE node software?',
)
@click.option('--unsafe', 'unsafe_ok', help='Allow unsafe update', hidden=True, is_flag=True)
@click.argument('env_file')
@streamed_cmd
def _update_passive(env_file, unsafe_ok):
    update_passive(env_file)


@passive_node.command('cleanup', help='Remove passive node data and containers')
@click.option(
    '--yes',
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt='Are you sure you want to remove all node containers and data?',
)
@streamed_cmd
def _cleanup_passive() -> None:
    cleanup_passive()
