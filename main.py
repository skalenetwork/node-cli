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
import sys
import logging
import inspect

from cli import __version__
from cli.info import BUILD_DATETIME, COMMIT, BRANCH, OS, VERSION
from cli.schains import schains_cli
from cli.containers import containers_cli
from cli.logs import logs_cli
from cli.node import node_cli
from cli.metrics import metrics_cli

from core.helper import (login_required, safe_load_texts, local_only,
                         no_node, init_default_logger)
from core.config import LONG_LINE
from core.wallet import get_wallet_info, set_wallet_by_pk
from core.user import (register_user, login_user, logout_user,
                       show_registration_token)
from core.host import (test_host, show_host, fix_url, reset_host,
                       init_logs_dir)
from tools.helper import session_config


config = session_config()
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


@cli.command('attach', help="Attach to remote SKALE node")
@click.argument('host')
@click.option('--skip-check', is_flag=True)
def attach(host, skip_check):
    host = fix_url(host)
    if not host:
        return
    if test_host(host) or skip_check:
        config['host'] = host
        logging.info(f'Attached to {host}')
        print(f'SKALE host: {host}')
    else:
        print(TEXTS['service']['node_host_not_valid'])


@cli.command('host', help="Get SKALE node endpoint")
@click.option('--reset', is_flag=True)
def host(reset):
    if reset:
        reset_host(config)
        return
    show_host(config)


@cli.group('user', help="SKALE node user commands")
def user():
    pass


@user.command('token',
              help="Show registration token if avaliable. "
                   "Server-only command.")
@click.option('--short', is_flag=True)
@local_only
def user_token(short):
    show_registration_token(short)


@user.command('register', help="Create new user for SKALE node")
@click.option(
    '--username', '-u',
    prompt="Enter username",
    help='SKALE node username'
)
@click.option(
    '--password', '-p',
    prompt="Enter password",
    help='SKALE node password',
    hide_input=True
)
@click.option(
    '--token', '-t',
    prompt="Enter one-time token",
    help='One-time token',
    hide_input=True
)
def register(username, password, token):
    register_user(config, username, password, token)


@user.command('login', help="Login user in a SKALE node")
@click.option(
    '--username', '-u',
    prompt="Enter username",
    help='SKALE node username'
)
@click.option(
    '--password', '-p',
    prompt="Enter password",
    help='SKALE node password',
    hide_input=True
)
def login(username, password):
    login_user(config, username, password)


@user.command('logout', help="Logout from SKALE node")
def logout():
    logout_user(config)


@cli.group('wallet', help="Node wallet commands")
def wallet():
    pass


@wallet.command('info', help="Get info about SKALE node wallet")
@click.option('--format', '-f', type=click.Choice(['json', 'text']))
@login_required
def wallet_info(format):
    config = session_config()
    get_wallet_info(config, format)


@wallet.command('set', help="Set local wallet for the SKALE node")
@click.option(
    '--private-key', '-p',
    prompt="Enter private key",
    help='Private key to be used as local wallet',
    hide_input=True
)
@login_required
@local_only
@no_node
def set_wallet(private_key):
    set_wallet_by_pk(private_key)


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
        sources=[cli, schains_cli, containers_cli, logs_cli,
                 node_cli, metrics_cli])
    try:
        cmd_collection()
    except Exception as err:
        print(f'Command execution falied with {err}. Recheck your inputs')
