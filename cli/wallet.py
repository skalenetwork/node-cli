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
