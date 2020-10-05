#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
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
import sys
import logging
import inspect
import traceback

from cli import __version__
from cli.containers import containers_cli
from cli.info import BUILD_DATETIME, COMMIT, BRANCH, OS, VERSION
from cli.logs import logs_cli
from cli.node import node_cli
from cli.schains import schains_cli
from cli.wallet import wallet_cli
from cli.ssl import ssl_cli
from cli.sgx import sgx_cli
from cli.exit import exit_cli
from cli.resources_allocation import resources_allocation_cli

from core.helper import (safe_load_texts, init_default_logger)
from configs import LONG_LINE
from core.host import init_logs_dir

TEXTS = safe_load_texts()

logger = logging.getLogger(__name__)


@click.group()
def cli():
    pass


@cli.command('version', help="Show SKALE node CLI version")
@click.option('--short', is_flag=True)
def version(short):
    if short:
        print(VERSION)
    else:
        print(f'SKALE Node CLI version: {VERSION}')


@cli.command('info', help="Show SKALE node CLI info")
def info():
    print(inspect.cleandoc(f'''
            {LONG_LINE}
            Version: {__version__}
            Full version: {VERSION}
            Build time: {BUILD_DATETIME}
            Build OS: {OS}
            Commit: {COMMIT}
            Git branch: {BRANCH}
            {LONG_LINE}
        '''))


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.error("Uncaught exception",
                 exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = handle_exception

if __name__ == '__main__':
    init_logs_dir()
    init_default_logger()
    args = sys.argv
    # todo: hide secret variables (passwords, private keys)
    logger.info(f'cmd: {" ".join(str(x) for x in args)}, v.{__version__}')

    cmd_collection = click.CommandCollection(
        sources=[cli, schains_cli, containers_cli, logs_cli, resources_allocation_cli,
                 node_cli, wallet_cli, ssl_cli, sgx_cli, exit_cli])
    try:
        cmd_collection()
    except Exception as err:
        print(f'Command execution failed with {err}. Recheck your inputs')
        traceback.print_exc()
        logger.error(err)
