import click
from readsettings import ReadSettings
from cli.helper import login_required, safe_load_texts, abort_if_false, server_only
from cli.config import CONFIG_FILEPATH
from cli.core import get_node_info, test_host, get_node_about, show_host
from cli.wallet import get_wallet_info
from cli.node import create_node, init, purge
from cli.user import register_user, login_user, logout_user, show_registration_token
from cli.host import install_host_dependencies

config = ReadSettings(CONFIG_FILEPATH)
TEXTS = safe_load_texts()


@click.group()
def cli():
    pass


@cli.command('setHost', help="Set SKALE node endpoint")
@click.argument('host')
@click.option('--skip-check', is_flag=True)
def set_host(host, skip_check):
    if test_host(host) or skip_check:
        config['host'] = host
        print(f'SKALE host: {host}')
    else:
        print(TEXTS['service']['node_host_not_valid'])


@cli.command('host', help="Get SKALE node endpoint")
def host():
    show_host(config)


@cli.group('node', help="SKALE node commands")
def node():
    pass


@cli.group('user', help="SKALE node user commands")
def user():
    pass


@user.command('token', help="Show registration token if avaliable. Server-only command.")
@server_only
def user_token():
    show_registration_token()


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


@node.command('info', help="Get info about SKALE node")
@click.option('--format', '-f', type=click.Choice(['json', 'text']))
@login_required
def node_info(format):
    get_node_info(config, format)


@node.command('about', help="Get service info about SKALE node")
@click.option('--format', '-f', type=click.Choice(['json', 'text']))
@login_required
def node_about(format):
    get_node_about(config, format)


@node.command('register', help="Register current node in the SKALE Manager")
@click.option(
    '--name', '-n',
    prompt="Enter node name",
    help='SKALE node name'
)
@click.option(
    '--p2p-ip',
    prompt="Enter node p2p IP",
    help='p2p IP for communication between nodes'
)
@click.option(
    '--public-ip',
    prompt="Enter node public IP",
    help='Public IP for RPC connections'
)
@click.option(
    '--port', '-p',
    prompt="Enter node base port",
    help='Base port for node sChains'
)
@login_required
def register_node(name, p2p_ip, public_ip, port):
    create_node(config, name, p2p_ip, public_ip, port)


@node.command('init', help="Initialize SKALE node")
@click.option('--install-deps', is_flag=True)
@click.option(  # todo: tmp option - after stable release branch
    '--git-branch',
    prompt="Enter Git branch to clone",
    help='Branch that will be used for SKALE node setup'
)
@click.option(  # todo: tmp option - remove after open source
    '--github-token',
    prompt="Enter GitHub access token",
    help='GitHub access token to clone the repo'
)
@click.option(  # todo: tmp option - remove after open source
    '--docker-username',
    prompt="Enter DockerHub username",
    help='DockerHub username to pull images'
)
@click.option(  # todo: tmp option - remove after open source
    '--docker-password',
    prompt="Enter DockerHub password",
    help='DockerHub password to pull images'
)
@click.option(  # todo: tmp option - remove after mainnet deploy
    '--rpc-ip',
    prompt="Enter Mainnet RPC IP",
    help='IP of the node in the network where SKALE manager is deployed'
)
@click.option(  # todo: tmp option - remove after mainnet deploy
    '--rpc-port',
    prompt="Enter Mainnet RPC port",
    help='WS RPC port of the node in the network where SKALE manager is deployed'
)
@click.option(
    '--db-user',
    prompt="Enter username for node DB",
    help='Username for node internal database'
)
@click.option(
    '--db-password',
    prompt="Enter password for node DB",
    help='Password for node internal database'
)
def init_node(install_deps, git_branch, github_token, docker_username, docker_password, rpc_ip,
              rpc_port, db_user,
              db_password):
    if install_deps:
        install_host_dependencies()
    init(git_branch, github_token, docker_username, docker_password, rpc_ip, rpc_port, db_user,
         db_password)


@node.command('purge', help="Uninstall SKALE node software from the machine")
@click.option('--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              prompt='Are you sure you want to uninstall SKALE node?')
def purge_node():
    purge()


@cli.group('wallet', help="Node wallet commands")
def wallet():
    pass


@wallet.command('info', help="Get info about SKALE node wallet")
@click.option('--format', '-f', type=click.Choice(['json', 'text']))
@login_required
def wallet_info(format):
    get_wallet_info(config, format)


if __name__ == '__main__':
    cli()