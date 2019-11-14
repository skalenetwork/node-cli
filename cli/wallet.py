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

import logging

import click

from core.helper import local_only, login_required, no_node
from core.wallet import get_wallet_info, set_wallet_by_pk

from tools.helper import session_config


logger = logging.getLogger(__name__)


@click.group()
def wallet_cli():
    pass


@wallet_cli.group('wallet', help="Node wallet commands")
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
