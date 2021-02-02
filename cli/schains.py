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

import click

from core.helper import abort_if_false
from core.schains import (
    describe,
    get_schain_firewall_rules,
    show_checks,
    show_config,
    show_dkg_info,
    show_schains,
    toggle_schain_repair_mode
)


@click.group()
def schains_cli() -> None:
    pass


@schains_cli.group('schains', help="Node sChains commands")
def schains() -> None:
    pass


@schains.command(help="List of sChains served by connected node")
def ls() -> None:
    show_schains()


@schains.command(help="DKG statuses for each sChain on the node")
@click.option(
    '--all', '-a', 'all_',
    help='Shows active and deleted sChains',
    is_flag=True
)
def dkg(all_: bool) -> None:
    show_dkg_info(all_)


@schains.command('config', help="sChain config")
@click.argument('schain_name')
def get_schain_config(schain_name: str) -> None:
    show_config(schain_name)


@schains.command('show-rules', help='Show schain firewall rules')
@click.argument('schain_name')
def show_rules(schain_name: str) -> None:
    get_schain_firewall_rules(schain_name)


@schains.command(help="List of healthchecks for sChains served by connected node")
@click.option(
    '--json',
    'json_format',
    help='Show data in JSON format',
    is_flag=True
)
def checks(json_format: bool) -> None:
    show_checks(json_format)


@schains.command('repair', help='Toggle schain repair mode')
@click.argument('schain_name')
@click.option('--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              prompt='Are you sure? Repair mode may corrupt working SKALE chain data.')
def repair(schain_name: str) -> None:
    toggle_schain_repair_mode(schain_name)


@schains.command('info', help='Show info about schain')
@click.argument('schain_name')
@click.option(
    '--json',
    'json_format',
    help='Show info in JSON format',
    is_flag=True
)
def info_(schain_name: str, json_format: bool) -> None:
    describe(schain_name, raw=json_format)
