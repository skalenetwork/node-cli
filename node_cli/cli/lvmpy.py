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

from lvmpy.src.app import run as run_lvmpy
from lvmpy.src.health import heal_service
from node_cli.utils.helper import abort_if_false

G_TEXTS = Texts()
TEXTS = G_TEXTS['lvmpy']


@click.group()
def lvmpy_cli():
    pass


@lvmpy_cli.group('lvmpy', help=TEXTS['help'])
def health():
    pass


@health.command(help=TEXTS['run']['help'])
@click.option(
    '--yes',
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt=TEXTS['run']['prompt']
)
def run():
    run_lvmpy()


@health.command(help=TEXTS['heal']['help'])
@click.option(
    '--yes',
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt=TEXTS['heal']['prompt']
)
def heal():
    heal_service()
