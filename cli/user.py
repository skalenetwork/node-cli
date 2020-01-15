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

from core.user import (register_user, login_user, logout_user,
                       show_registration_token)
from tools.helper import session_config


logger = logging.getLogger(__name__)


@click.group()
def user_cli():
    pass


@user_cli.group(help="SKALE identity manipulation commands")
def user():
    pass


@user.command('token',
              help="Show registration token if avaliable. "
                   "Server-only command.")
@click.option('--short', is_flag=True)
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
    config = session_config()
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
    config = session_config()
    login_user(config, username, password)


@user.command('logout', help="Logout from SKALE node")
def logout():
    config = session_config()
    logout_user(config)
