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

from node_cli.cli.info import TYPE
from node_cli.fair.common import cleanup as cleanup_fair
from node_cli.fair.common import init as init_fair
from node_cli.fair.common import turn_off as turn_off_fair
from node_cli.fair.common import turn_on as turn_on_fair
from node_cli.fair.common import update as update_fair
from node_cli.fair.passive import setup_fair_passive
from node_cli.utils.helper import (
    URL_OR_ANY_TYPE,
    abort_if_false,
    error_exit,
    streamed_cmd,
)
from node_cli.utils.node_type import NodeMode
from node_cli.utils.texts import safe_load_texts

TEXTS = safe_load_texts()


@click.group()
def passive_fair_node_cli():
    pass


@passive_fair_node_cli.group(help='Commands for passive Fair Node operations.')
def passive_node():
    pass


@passive_node.command('init', help='Initialize a passive Fair node')
@click.argument('config_file')
@click.option('--id', required=True, type=int, help=TEXTS['fair']['node']['setup']['id'])
@click.option('--indexer', help=TEXTS['passive_node']['init']['indexer'], is_flag=True)
@click.option('--archive', help=TEXTS['passive_node']['init']['archive'], is_flag=True)
@click.option(
    '--snapshot',
    type=URL_OR_ANY_TYPE,
    default=None,
    help=TEXTS['passive_node']['init']['snapshot_from'],
)
@streamed_cmd
def init_passive_node(
    config_file: str, id: int, indexer: bool, archive: bool, snapshot: str | None
):
    if indexer and archive:
        error_exit('Cannot use both --indexer and --archive options')
    if (indexer or archive) and snapshot == 'any':
        error_exit('Cannot use any for indexer/archive node')
    init_fair(
        node_mode=NodeMode.PASSIVE,
        config_file=config_file,
        node_id=id,
        indexer=indexer,
        archive=archive,
        snapshot=snapshot,
    )


@passive_node.command('update', help='Update Fair node')
@click.argument('config_file')
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
def update_node(config_file: str, pull_config_for_schain, force_skaled_start: bool):
    update_fair(
        node_mode=NodeMode.PASSIVE,
        config_file=config_file,
        pull_config_for_schain=pull_config_for_schain,
        force_skaled_start=force_skaled_start,
    )


@passive_node.command('cleanup', help='Remove all FAIR node data and containers.')
@click.option(
    '--yes',
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt='Are you sure you want to remove all FAIR node data and containers?',
)
@click.option('--prune', is_flag=True, help='Prune docker system.')
@streamed_cmd
def cleanup_node(prune):
    cleanup_fair(node_mode=NodeMode.PASSIVE, prune=prune)


@passive_node.command('setup', help=TEXTS['fair']['node']['setup']['help'])
@click.option('--id', required=True, type=int, help=TEXTS['fair']['node']['setup']['id'])
def _setup(id: int) -> None:
    setup_fair_passive(node_id=id)


@passive_node.command('turn-off', help='Turn off the node')
@click.option(
    '--yes',
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt='Are you sure you want to turn off the node?',
)
@streamed_cmd
def turn_off_node() -> None:
    turn_off_fair(node_type=TYPE)


@passive_node.command('turn-on', help='Turn on the node')
@click.option(
    '--yes',
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt='Are you sure you want to turn on the node?',
)
@click.argument('config_file')
@streamed_cmd
def turn_on_node(config_file: str) -> None:
    turn_on_fair(env_file=config_file, node_type=TYPE)
