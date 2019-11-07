import logging

import click

from core.helper import local_only

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
