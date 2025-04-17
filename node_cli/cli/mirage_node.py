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

from node_cli.utils.helper import (
    safe_load_texts,
)


G_TEXTS = safe_load_texts()
TEXTS = G_TEXTS['mirage']


@click.group('node', help='Commands for the Mirage node.')
def mirage_node_cli():
    pass


@mirage_node_cli.group(help='Mirage node commands')
def mirage():
    pass
