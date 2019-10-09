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
from core.helper import login_required, get
from core.print_formatters import print_metrics


@click.group()
def metrics_cli():
    pass


@metrics_cli.group('metrics', help="Node metrics commands")
def metrics():
    pass


@metrics.command(help="List of bounties and metrics for the first year")
@login_required
def first():
    print('Please wait - collecting metrics from blockchain...')
    bounty_data = get('first-bounties')
    if not bounty_data.get('bounties'):
        print('No bounties found')
        return
    print_metrics(bounty_data)


@metrics.command(help="List of bounties and metrics for the last year")
@login_required
def last():
    print('Please wait - collecting metrics from blockchain...')
    bounty_data = get('last-bounties')
    if not bounty_data.get('bounties'):
        print('No bounties found')
        return
    print_metrics(bounty_data)
