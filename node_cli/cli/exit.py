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

import logging

import click

from node_cli.core.print_formatters import print_exit_status
from node_cli.utils.helper import error_exit, get_request, post_request, abort_if_false
from node_cli.utils.exit_codes import CLIExitCodes
from node_cli.utils.texts import Texts

logger = logging.getLogger(__name__)
TEXTS = Texts()
BLUEPRINT_NAME = 'node'


@click.group()
def exit_cli():
    pass


@exit_cli.group('exit', help="Exit commands")
def node_exit():
    pass


@node_exit.command('start', help="Start exiting process")
@click.option('--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              prompt='Are you sure you want to destroy your SKALE node?')
def start():
    status, payload = post_request(
        blueprint=BLUEPRINT_NAME,
        method='exit/start'
    )
    if status == 'ok':
        msg = TEXTS['exit']['start']
        logger.info(msg)
        print(msg)
    else:
        error_exit(payload, exit_code=CLIExitCodes.BAD_API_RESPONSE)


@node_exit.command('status', help="Get exit process status")
@click.option('--format', '-f', type=click.Choice(['json', 'text']))
def status(format):
    status, payload = get_request(
        blueprint=BLUEPRINT_NAME,
        method='exit/status'
    )
    if status == 'ok':
        exit_status = payload
        if format == 'json':
            print(exit_status)
        else:
            print_exit_status(exit_status)
    else:
        error_exit(payload, exit_code=CLIExitCodes.BAD_API_RESPONSE)


@node_exit.command('finalize', help="Finalize exit process")
def finalize():
    pass
