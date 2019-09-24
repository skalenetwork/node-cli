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

import ipaddress
from urllib.parse import urlparse

import click
from readsettings import ReadSettings

from skale.utils.random_names.generator import generate_random_node_name

from core.core import get_node_info, get_node_about
from core.node import create_node, init, purge, update
from core.host import install_host_dependencies
from core.helper import (abort_if_false, local_only,
                         login_required, safe_load_texts)
from core.config import CONFIG_FILEPATH, DEFAULT_RPC_IP, DEFAULT_RPC_PORT, \
    DEFAULT_DB_USER, DEFAULT_DB_PORT, DEFAULT_MTA_ENDPOINT, DEFAULT_ENDPOINT
from configs.node import DEFAULT_NODE_BASE_PORT

config = ReadSettings(CONFIG_FILEPATH)
TEXTS = safe_load_texts()


class UrlType(click.ParamType):
    name = 'url'

    def convert(self, value, param, ctx):
        try:
            result = urlparse(value)
        except ValueError:
            self.fail(f'Some characters are not allowed in {value}',
                      param, ctx)
        if not all([result.scheme, result.netloc]):
            self.fail(f'Expected valid url. Got {value}', param, ctx)
        return value


class IpType(click.ParamType):
    name = 'ip'

    def convert(self, value, param, ctx):
        try:
            ipaddress.ip_address(value)
        except ValueError:
            self.fail(f'expected valid ipv4/ipv6 address. Got {value}',
                      param, ctx)
        return value


URL_TYPE = UrlType()
IP_TYPE = IpType()


@click.group()
def node_cli():
    pass


@node_cli.group(help="SKALE node commands")
def node():
    pass


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
    # prompt="Enter node name",
    default=generate_random_node_name(),
    help='SKALE node name'
)
# @click.option(
#     '--p2p-ip',
#     prompt="Enter node p2p IP",
#     help='p2p IP for communication between nodes'
# )
# @click.option(
#     '--public-ip',
#     prompt="Enter node public IP",
#     help='Public IP for RPC connections'
# )
@click.option(
    '--ip',
    prompt="Enter node public IP",
    type=IP_TYPE,
    help='Public IP for RPC connections & consensus (required)'
)
@click.option(
    '--port', '-p',
    default=DEFAULT_NODE_BASE_PORT,
    type=int,
    # prompt="Enter node base port",
    help='Base port for node sChains'
)
@login_required
# def register_node(name, p2p_ip, public_ip, port):
def register_node(name, ip, port):
    create_node(config, name, ip, ip, port)


@node.command('init', help="Initialize SKALE node")
@click.option('--install-deps', is_flag=True)
@click.option(  # todo: tmp option - after stable release branch
    '--mta-endpoint',
    type=URL_TYPE,
    # prompt="Enter Git branch to clone",
    help='MTA endpoint to connect',
    default=DEFAULT_MTA_ENDPOINT
)
@click.option(  # todo: tmp option - after stable release branch
    '--stream',
    prompt="Enter stream for the SKALE node",
    help='Stream that will be used for SKALE node setup (required)'
)
@click.option(  # todo: tmp option - remove after open source
    '--github-token',
    prompt="Enter GitHub access token",
    help='GitHub access token to clone the repo (required)'
)
@click.option(  # todo: tmp option - remove after open source
    '--docker-username',
    prompt="Enter DockerHub username",
    help='DockerHub username to pull images (required)'
)
@click.option(  # todo: tmp option - remove after open source
    '--docker-password',
    prompt="Enter DockerHub password",
    help='DockerHub password to pull images (required)'
)
@click.option(  # todo: tmp option - remove after mainnet deploy
    '--endpoint',
    type=URL_TYPE,
    # prompt="Enter Mainnet RPC port",
    help='RPC endpoint of the node in the network '
         'where SKALE manager is deployed',
    default=DEFAULT_ENDPOINT
)
@click.option(  # todo: tmp option - remove after mainnet deploy
    '--rpc-ip',
    type=IP_TYPE,
    # prompt="Enter Mainnet RPC IP",
    help='IP of the node in the network where SKALE manager is deployed',
    default=DEFAULT_RPC_IP
)
@click.option(  # todo: tmp option - remove after mainnet deploy
    '--rpc-port',
    type=int,
    # prompt="Enter Mainnet RPC port",
    help='WS RPC port of the node in the network '
         'where SKALE manager is deployed',
    default=DEFAULT_RPC_PORT
)
@click.option(
    '--db-user',
    # prompt="Enter username for node DB",
    help='Username for node internal database',
    default=DEFAULT_DB_USER
)
@click.option(
    '--db-password',
    prompt="Enter password for node DB",
    help='Password for node internal database (required)'
)
@click.option(
    '--db-root-password',
    # prompt="Enter root password for node DB",
    help='Password for root user of node internal database'
)
@click.option(
    '--db-port',
    type=int,
    help='Port for of node internal database',
    default=DEFAULT_DB_PORT
)
@click.option(
    '--disk-mountpoint',
    prompt="Enter data disk mount point",
    help='Mount point of the disk to be used '
         'for storing sChains data (required)'
)
@click.option(
    '--test-mode',
    is_flag=True
)
@local_only
def init_node(mta_endpoint, install_deps, stream, github_token,
              docker_username, docker_password, endpoint, rpc_ip,
              rpc_port, db_user, db_password, db_root_password, db_port,
              disk_mountpoint, test_mode):
    if install_deps:
        install_host_dependencies()
    if not db_root_password:
        db_root_password = db_password

    git_branch = stream
    init(mta_endpoint, git_branch, github_token, docker_username,
         docker_password, endpoint, rpc_ip, rpc_port, db_user,
         db_password, db_root_password, db_port, disk_mountpoint, test_mode)


@node.command('purge', help="Uninstall SKALE node software from the machine")
@click.option('--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              prompt='Are you sure you want to uninstall SKALE node?')
@local_only
def purge_node():
    purge()


# @node.command('deregister', help="De-register node from the SKALE Manager")
# @click.option('--yes', is_flag=True, callback=abort_if_false,
#               expose_value=False,
#               prompt='Are you sure you want to de-register '
#                      'this node from SKALE Manager?')
# @local_only
# def deregister_node():
#     deregister()


@node.command('update', help="De-register node from the SKALE Manager")
@click.option('--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              prompt='Are you sure you want to update SKALE node software?')
@click.option(  # todo: tmp option - after stable release branch
    '--mta-endpoint',
    type=URL_TYPE,
    # prompt="Enter Git branch to clone",
    help='MTA endpoint to connect',
    default=DEFAULT_MTA_ENDPOINT
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
    '--endpoint',
    type=URL_TYPE,
    # prompt="Enter Mainnet RPC port",
    help='RPC endpoint of the node in the network '
         'where SKALE manager is deployed',
    default=DEFAULT_ENDPOINT
)
@click.option(  # todo: tmp option - remove after mainnet deploy
    '--rpc-ip',
    type=IP_TYPE,
    # prompt="Enter Mainnet RPC IP",
    help='IP of the node in the network where SKALE manager is deployed',
    default=DEFAULT_RPC_IP
)
@click.option(  # todo: tmp option - remove after mainnet deploy
    '--rpc-port',
    type=int,
    # prompt="Enter Mainnet RPC port",
    help='WS RPC port of the node in the network '
         'where SKALE manager is deployed',
    default=DEFAULT_RPC_PORT
)
@click.option(
    '--db-user',
    # prompt="Enter username for node DB",
    help='Username for node internal database',
    default=DEFAULT_DB_USER
)
@click.option(
    '--db-password',
    prompt="Enter password for node DB",
    help='Password for node internal database'
)
@click.option(
    '--db-root-password',
    # prompt="Enter root password for node DB",
    help='Password for root user of node internal database'
)
@click.option(
    '--db-port',
    type=int,
    help='Port for of node internal database',
    default=DEFAULT_DB_PORT
)
@local_only
def update_node(mta_endpoint, github_token, docker_username, docker_password,
                endpoint, rpc_ip, rpc_port,
                db_user, db_password, db_root_password, db_port):
    if not db_root_password:
        db_root_password = db_password
    update(mta_endpoint, github_token, docker_username, docker_password,
           endpoint, rpc_ip, rpc_port,
           db_user, db_password, db_root_password, db_port)
