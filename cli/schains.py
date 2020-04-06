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
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

import click
import pprint
from core.helper import get
from core.print_formatters import print_schains, print_dkg_statuses, print_schains_healthchecks


@click.group()
def schains_cli():
    pass


@schains_cli.group('schains', help="Node sChains commands")
def schains():
    pass


@schains.command(help="List of sChains served by connected node")
def ls():
    schains_list = get('node_schains')
    if not schains_list:
        print('No sChains found')
        return
    print_schains(schains_list)


@schains.command(help="DKG statuses for each sChain on the node")
@click.option(
    '--all',
    help='Shows active and deleted sChains',
    is_flag=True
)
def dkg(all):
    if all:
        dkg_statuses = get('dkg_statuses', params={'all': True})
    else:
        dkg_statuses = get('dkg_statuses')
    if not dkg_statuses:
        return
    print_dkg_statuses(dkg_statuses)


@schains.command('config', help="sChain config")
@click.argument('schain_name')
def get_schain_config(schain_name):
    schain_config = get('schain_config', {'schain-name': schain_name})
    if not schain_config:
        return
    pprint.pprint(schain_config)


@schains.command(help="List of healthchecks for sChains served by connected node")
@click.option(
    '--json',
    'json_format',
    help='Show data in JSON format',
    is_flag=True
)
def checks(json_format):
    schains_healthchecks_list = get('schains_healthchecks')
    if not schains_healthchecks_list:
        print('No sChains found')
        return

    if json_format:
        print(schains_healthchecks_list)
    else:
        print_schains_healthchecks(schains_healthchecks_list)
