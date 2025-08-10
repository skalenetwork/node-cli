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

from node_cli.fair import init as init_fair
from node_cli.fair import update as update_fair
from node_cli.fair import cleanup as cleanup_fair
from node_cli.utils.helper import abort_if_false, streamed_cmd
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
@click.argument('env_filepath')
@streamed_cmd
def init_passive_node(env_filepath: str):
    init_fair(node_mode=NodeMode.PASSIVE, env_filepath=env_filepath)


@passive_node.command('update', help='Update Fair node')
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


@passive_node.command('cleanup', help='Cleanup Fair node.')
@click.option(
    '--yes',
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt='Are you sure you want to cleanup Fair node?',
)
@streamed_cmd
def cleanup_node():
    cleanup_fair()
