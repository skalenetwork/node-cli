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

import click

from node_cli.core.node import init_sync, update_sync
from node_cli.utils.helper import abort_if_false, safe_load_texts, streamed_cmd


TEXTS = safe_load_texts()


@click.group()
def sync_node_cli():
    pass


@sync_node_cli.group(help="SKALE sync node commands")
def sync_node():
    pass


@sync_node.command('init', help="Initialize sync SKALE node")
@click.argument('env_file')
@streamed_cmd
def _init_sync(env_file):
    init_sync(env_file)


@sync_node.command('update', help='Update sync node from .env file')
@click.option('--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              prompt='Are you sure you want to update SKALE node software?')
@click.argument('env_file')
@streamed_cmd
def _update_sync(env_file):
    update_sync(env_file)
