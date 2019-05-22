import click
from readsettings import ReadSettings
from cli.helper import login_required, safe_load_texts
from cli.config import CONFIG_FILEPATH
from cli.core import login_user, get_node_info, logout_user, test_host

config = ReadSettings(CONFIG_FILEPATH)
TEXTS = safe_load_texts()


@click.group()
def cli():
    pass


@cli.command('setHost', help="Set SKALE node endpoint")
@click.argument('host')
def set_host(host):
    if test_host(host):
        config['host'] = host
        print(f'SKALE host: {host}')
    else:
        print(TEXTS['service']['node_host_not_valid'])


@cli.group('node', help="SKALE node commands")
def node():
    pass


@cli.command('login', help="Login user in a SKALE node")
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


@cli.command('logout', help="Logout from SKALE node")
def logout():
    logout_user(config)


@node.command('info', help="Get info about SKALE node")
@click.option('--format', '-f', type=click.Choice(['json', 'text']))
@login_required
def node(format):
    get_node_info(config, format)


if __name__ == '__main__':
    cli()
