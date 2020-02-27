#   -*- coding: utf-8 -*-
#
#   This file is part of skale-node-cli
#
#   Copyright (C) 2019-2020 SKALE Labs
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
from core.helper import get
from core.print_formatters import print_metrics
from core.texts import Texts

G_TEXTS = Texts()
TEXTS = G_TEXTS['metrics']


@click.group()
def metrics_cli():
    pass


@metrics_cli.group('metrics', invoke_without_command=True, help="Node metrics commands")
@click.option(
    '--since', '-s',
    type=click.DateTime(formats=['%Y-%m-%d']),
    help=TEXTS['since']['help']
)
@click.option(
    '--till', '-t',
    type=click.DateTime(formats=['%Y-%m-%d']),
    help=TEXTS['till']['help']
)
@click.option(
    '--limit', '-l',
    type=int,
    help=TEXTS['limit']['help']
)
@click.option('--fast', '-f', is_flag=True)
@click.pass_context
def metrics(ctx, since, till, limit, fast):
    if ctx.invoked_subcommand is None:
        print(TEXTS['wait_msg'])
        data = get('metrics', {'since': since, 'till': till, 'limit': limit, 'fast': fast})
        metrics = data['metrics']
        total_bounty = data['total']
        print_metrics(metrics, total_bounty)
