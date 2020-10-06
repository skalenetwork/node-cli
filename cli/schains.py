#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
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

import json
import pprint

import click

from core.helper import get_request
from core.print_formatters import (print_err_response, print_schains,
                                   print_dkg_statuses, print_schains_healthchecks)
from core.schains import get_schain_firewall_rules


@click.group()
def schains_cli():
    pass


@schains_cli.group('schains', help="Node sChains commands")
def schains():
    pass


@schains.command(help="List of sChains served by connected node")
def ls():
    status, payload = get_request('node_schains')

    if status == 'ok':
        schains_list = payload
        if not schains_list:
            print('No sChains found')
            return
        print_schains(schains_list)
    else:
        print_err_response(payload)


@schains.command(help="DKG statuses for each sChain on the node")
@click.option(
    '--all',
    help='Shows active and deleted sChains',
    is_flag=True
)
def dkg(all):
    params = {'all': all}
    status, payload = get_request('dkg_statuses', params=params)
    if status == 'ok':
        print_dkg_statuses(payload)
    else:
        print_err_response(payload)


@schains.command('config', help="sChain config")
@click.argument('schain_name')
def get_schain_config(schain_name):
    status, payload = get_request('schain_config', {'schain-name': schain_name})
    if status == 'ok':
        pprint.pprint(payload)
    else:
        print_err_response(payload)


@schains.command('show-rules', help='Show schain firewall rules')
@click.argument('schain_name')
def show_rules(schain_name):
    get_schain_firewall_rules(schain_name)


@schains.command(help="List of healthchecks for sChains served by connected node")
@click.option(
    '--json',
    'json_format',
    help='Show data in JSON format',
    is_flag=True
)
def checks(json_format):
    status, payload = get_request('schains_healthchecks')
    if status == 'ok':
        if not payload:
            print('No sChains found')
            return
        if json_format:
            print(json.dumps(payload))
        else:
            print_schains_healthchecks(payload)
    else:
        print_err_response(payload)
