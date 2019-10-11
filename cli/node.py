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

from skale.utils.random_names.generator import generate_random_node_name

from core.core import get_node_info, get_node_about
from core.node import create_node, init, purge, update
from core.host import install_host_dependencies
from core.helper import (abort_if_false, local_only,
                         login_required, safe_load_texts)
from core.config import DEFAULT_DB_USER, DEFAULT_DB_PORT
from configs.node import DEFAULT_NODE_BASE_PORT
from tools.helper import session_config

config = session_config()
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
    config = session_config()
    get_node_info(config, format)


@node.command('about', help="Get service info about SKALE node")
@click.option('--format', '-f', type=click.Choice(['json', 'text']))
@login_required
def node_about(format):
    config = session_config()
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
    config = session_config()
    create_node(config, name, ip, ip, port)


@node.command('init', help="Initialize SKALE node")
@click.option('--install-deps', is_flag=True)
@click.option(
    '--ima-endpoint',
    type=URL_TYPE,
    prompt="Enter IMA endpoint to connect",
    help='IMA endpoint to connect'
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
    prompt="Enter Mainnet RPC endpoint",
    help='RPC endpoint of the node in the network '
         'where SKALE manager is deployed'
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
    '--manager-url',
    prompt="Enter URL to SKALE Manager contracts ABI and addresses",
    help='URL to SKALE Manager contracts ABI and addresses'
)
@click.option(
    '--ima-url',
    prompt="Enter URL to IMA contracts ABI and addresses",
    help='URL to IMA contracts ABI and addresses'
)
@click.option(
    '--dkg-url',
    prompt="Enter URL to DKG contracts ABI and addresses",
    help='URL to DKG contracts ABI and addresses'
)
@click.option(
    '--filebeat-url',
    prompt="Enter URL to the Filebeat log server",
    help='URL to the Filebeat log server'
)
@click.option(
    '--test-mode',
    is_flag=True
)
@local_only
def init_node(ima_endpoint, install_deps, stream, github_token, docker_username, docker_password,
              endpoint, db_user, db_password, db_root_password, db_port, disk_mountpoint,
              manager_url, ima_url, dkg_url, filebeat_url, test_mode):
    if install_deps:
        install_host_dependencies()
    if not db_root_password:
        db_root_password = db_password

    git_branch = stream
    init(ima_endpoint, git_branch, github_token, docker_username, docker_password, endpoint,
         db_user, db_password, db_root_password, db_port, disk_mountpoint, manager_url, ima_url,
         dkg_url, filebeat_url, test_mode)


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
    '--ima-endpoint',
    type=URL_TYPE,
    prompt="Enter IMA endpoint to connect",
    help='IMA endpoint to connect',
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
    prompt="Enter Mainnet RPC port",
    help='RPC endpoint of the node in the network '
         'where SKALE manager is deployed',
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
@click.option(
    '--manager-url',
    prompt="Enter URL to SKALE Manager contracts ABI and addresses",
    help='URL to SKALE Manager contracts ABI and addresses'
)
@click.option(
    '--ima-url',
    prompt="Enter URL to IMA contracts ABI and addresses",
    help='URL to IMA contracts ABI and addresses'
)
@click.option(
    '--dkg-url',
    prompt="Enter URL to DKG contracts ABI and addresses",
    help='URL to DKG contracts ABI and addresses'
)
@click.option(
    '--filebeat-url',
    prompt="Enter URL to the Filebeat log server",
    help='URL to the Filebeat log server'
)
@local_only
def update_node(ima_endpoint, github_token, docker_username, docker_password, endpoint, db_user,
                db_password, db_root_password, db_port, manager_url, ima_url, dkg_url,
                filebeat_url):
    if not db_root_password:
        db_root_password = db_password
    update(ima_endpoint, github_token, docker_username, docker_password, endpoint, db_user,
           db_password, db_root_password, db_port, manager_url, ima_url, dkg_url, filebeat_url)
