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

import sys

import click
from node_cli.core.logs import create_logs_dump
from node_cli.configs.cli_logger import LOG_FILEPATH, DEBUG_LOG_FILEPATH
from node_cli.utils.exit_codes import CLIExitCodes


@click.group()
def logs_cli():
    pass


@logs_cli.group(help="Logs commands")
def logs():
    pass


@logs.command(help="Fetch the logs of the node-cli")
@click.option('--debug', is_flag=True)
def cli(debug):
    filepath = DEBUG_LOG_FILEPATH if debug else LOG_FILEPATH
    with open(filepath, 'r') as fin:
        print(fin.read())


@logs.command(help="Dump all logs from the connected node")
@click.option(
    '--container',
    '-c',
    help='Dump logs only from specified container',
    default=None
)
@click.argument('path')
def dump(container, path):
    res = create_logs_dump(path, container)
    if res:
        print(f'Logs dump created: {res}')
    else:
        sys.exit(CLIExitCodes.OPERATION_EXECUTION_ERROR)
