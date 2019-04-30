import click
from readsettings import ReadSettings
from cli.config import CONFIG_FILEPATH
from cli.core import login_user, get_node_info

config = ReadSettings(CONFIG_FILEPATH)


@click.group()
def cli():
    pass


@cli.command('setHost', help="Set SKALE node endpoint")
@click.argument('host')
def set_host(host):
    # todo: test connection to the skale node
    # validate_node_host(host)
    config['host'] = host
    print(f'SKALE host: {host}')


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
    hide_input=True,
    # confirmation_prompt=True
)
def login(username, password):
    login_user(config, username, password)


@node.command('info', help="Get info about SKALE node")
@click.option('--format', '-f', type=click.Choice(['json', 'text']))
def node(format):
    get_node_info(config, format)


if __name__ == '__main__':
    cli()
