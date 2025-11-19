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

from node_cli.fair.chain import get_chain_record, get_chain_checks


@click.group()
def chain_cli():
    pass


@chain_cli.group(help='Fair chain commands')
def chain():
    pass


@chain.command('record', help='Get Fair chain record information')
@click.option('--json', 'raw', is_flag=True, help='Output in JSON format')
def chain_record(raw: bool) -> None:
    get_chain_record(raw=raw)


@chain.command('checks', help='Get Fair chain checks status')
@click.option('--json', 'raw', is_flag=True, help='Output in JSON format')
def chain_checks(raw: bool) -> None:
    get_chain_checks(raw=raw)
