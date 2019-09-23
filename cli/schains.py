#   -*- coding: utf-8 -*-
#
#   This file is part of skale-node-cli
#
#   Copyright (C) 2019 SKALE Labs
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

import click
import pprint
from core.helper import login_required, get
from core.print_formatters import print_schains


@click.group()
def schains_cli():
    pass


@schains_cli.group('schains', help="Node sChains commands")
def schains():
    pass


@schains.command(help="List of sChains served by connected node")
@login_required
def ls():
    schains_list = get('node_schains')
    if not schains_list:
        print('No sChains found')
        return
    print_schains(schains_list)


@schains.command('config', help="sChain config")
@click.argument('schain_name')
@login_required
def get_schain_config(schain_name):
    schain_config = get('schain_config', {'schain-name': schain_name})
    if not schain_config:
        return
    pprint.pprint(schain_config)
