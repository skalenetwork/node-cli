#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
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
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

import ipaddress
from urllib.parse import urlparse

import click

from node_cli.core.node import (
    configure_firewall_rules,
    get_node_signature,
    init,
    restore,
    register_node as register,
    update,
    backup,
    set_maintenance_mode_on,
    set_maintenance_mode_off,
    turn_off,
    turn_on,
    get_node_info,
    set_domain_name,
    run_checks
)
from node_cli.configs import DEFAULT_NODE_BASE_PORT
from node_cli.configs.env import ALLOWED_ENV_TYPES
from node_cli.utils.decorators import check_inited
from node_cli.utils.helper import (
    abort_if_false,
    safe_load_texts,
    streamed_cmd
)
from node_cli.utils.meta import get_meta_info
from node_cli.utils.print_formatters import print_meta_info


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
def node_info(format):
    get_node_info(format)


@node.command('register', help="Register current node in the SKALE Manager")
@click.option(
    '--name', '-n',
    required=True,
    prompt="Enter node name",
    help='SKALE node name'
)
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
    help='Base port for node sChains'
)
@click.option(
    '--domain', '-d',
    prompt="Enter node domain name",
    type=str,
    help='Node domain name'
)
@streamed_cmd
def register_node(name, ip, port, domain):
    register(name, ip, ip, port, domain)


@node.command('init', help="Initialize SKALE node")
@click.argument('env_file')
@streamed_cmd
def init_node(env_file):
    init(env_file)


@node.command('update', help='Update node from .env file')
@click.option('--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              prompt='Are you sure you want to update SKALE node software?')
@click.argument('env_file')
@streamed_cmd
def update_node(env_file):
    update(env_file)


@node.command('signature', help='Get node signature for given validator id')
@click.argument('validator_id')
def signature(validator_id):
    res = get_node_signature(validator_id)
    print(f'Signature: {res}')


@node.command('backup', help="Generate backup file to restore SKALE node on another machine")
@click.argument('backup_folder_path')
@streamed_cmd
def backup_node(backup_folder_path):
    backup(backup_folder_path)


@node.command('restore', help="Restore SKALE node on another machine")
@click.argument('backup_path')
@click.argument('env_file')
@streamed_cmd
def restore_node(backup_path, env_file):
    restore(backup_path, env_file)


@node.command('maintenance-on', help="Set SKALE node into maintenance mode")
@click.option('--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              prompt='Are you sure you want to set SKALE node into maintenance mode?')
@streamed_cmd
def set_node_in_maintenance():
    set_maintenance_mode_on()


@node.command('maintenance-off', help="Remove SKALE node from maintenance mode")
@streamed_cmd
def remove_node_from_maintenance():
    set_maintenance_mode_off()


@node.command('turn-off', help='Turn off the node')
@click.option(
    '--maintenance-on',
    help='Set SKALE node into maintenance mode before turning off',
    is_flag=True
)
@click.option('--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              prompt='Are you sure you want to turn off the node?')
@streamed_cmd
def _turn_off(maintenance_on):
    turn_off(maintenance_on)


@node.command('turn-on', help='Turn on the node')
@click.option(
    '--maintenance-off',
    help='Turn off maintenance mode after turning on the node',
    is_flag=True
)
@click.option(
    '--sync-schains',
    help='Run all sChains in the snapshot download mode',
    is_flag=True,
    hidden=True
)
@click.option('--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              prompt='Are you sure you want to turn on the node?')
@click.argument('env_file')
@streamed_cmd
def _turn_on(maintenance_off, sync_schains, env_file):
    turn_on(maintenance_off, sync_schains, env_file)


@node.command('set-domain', help="Set node domain name")
@click.option(
    '--domain', '-d',
    prompt="Enter node domain name",
    type=str,
    help='Node domain name'
)
@click.option('--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              prompt='Are you sure you want to set domain name?')
@streamed_cmd
def _set_domain_name(domain):
    set_domain_name(domain)


@node.command(help='Check if node meet network requirements')
@click.option(
    '--network', '-n',
    type=click.Choice(ALLOWED_ENV_TYPES),
    default='mainnet',
    help='Network to check'
)
def check(network):
    run_checks(network)


@node.command(help='Reconfigure iptables rules')
@click.option('--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              prompt='Are you sure you want to reconfigure firewall rules?')
def configure_firewall():
    configure_firewall_rules()


@node.command(help='Show node version information')
@check_inited
@click.option(
    '--json',
    'raw',
    is_flag=True,
    help=TEXTS['common']['json']
)
def version(raw: bool) -> None:
    meta_info = get_meta_info(raw=raw)
    if raw:
        print(meta_info)
    else:
        print_meta_info(meta_info)
