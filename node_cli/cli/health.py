#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
#
#   Copyright (C) 2020 SKALE Labs
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
from node_cli.utils.texts import Texts

from node_cli.core.health import get_containers, get_schains_checks, get_sgx_info


G_TEXTS = Texts()
TEXTS = G_TEXTS['health']


@click.group()
def health_cli():
    pass


@health_cli.group('health', help=TEXTS['help'])
def health():
    pass


@health.command(help=TEXTS['containers']['help'])
@click.option('--all', '-a', is_flag=True)
def containers(all):
    get_containers(_all=all)


@health.command(help=TEXTS['schains_checks']['help'])
@click.option(
    '--json',
    'json_format',
    help=G_TEXTS['common']['json'],
    is_flag=True
)
def schains(json_format: bool) -> None:
    get_schains_checks(json_format)


@health.command(help=TEXTS['sgx']['help'])
def sgx():
    get_sgx_info()
