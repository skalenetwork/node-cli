#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
#
#   Copyright (C) 2019-Present SKALE Labs
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

from node_cli.core.fair import fair_node_exit
from node_cli.utils.decorators import check_inited
from node_cli.utils.helper import abort_if_false, streamed_cmd


@click.group()
def fair_cli():
    pass


@fair_cli.group(help="Fair node commands")
def fair():
    pass


@fair.group(help="Fair node management")
def node():
    pass


@node.command('exit', help="Remove node from fair manager contracts")
@click.option('--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              prompt='Are you sure you want to remove this node from fair manager contracts?')
@check_inited
@streamed_cmd
def fair_node_exit_cmd():
    fair_node_exit()