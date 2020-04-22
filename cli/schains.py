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
from core.print_formatters import print_schains, print_dkg_statuses
from core.schains import (get_schain_firewall_rules,
                          turn_off_schain_firewall_rules, turn_on_schain_firewall_rules)


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


@schains.command('show-rules', help='Show schain firewall rules')
@click.argument('schain_name')
def show_rules(schain_name):
    rules = get_schain_firewall_rules(schain_name)
    formated_rules = []
    for r in rules:
        if r["ip"] is not None:
            formated_rules.append(f'Ip: {r["ip"]} Port: {r["port"]}')
        else:
            formated_rules.append(f'Port: {r["port"]}')

    print('Allowed endpoints')
    print('\n'.join(sorted(formated_rules)))


@schains.command('turn-on-rules', help='Turn on schain firewall rules')
@click.argument('schain_name')
def turn_on_rules(schain_name):
    turn_on_schain_firewall_rules(schain_name)
    print('Success')


@schains.command('turn-off-rules', help='Turn off schain firewall rules')
@click.argument('schain_name')
def turn_off_rules(schain_name):
    turn_off_schain_firewall_rules(schain_name)
    print('Success')
