#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
#
#   Copyright (C) 2021 SKALE Labs
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

import logging
import socket
import sys
from pathlib import Path

from node_cli.configs import IPTABLES_DIR, IPTABLES_RULES_STATE_FILEPATH, ENV
from node_cli.utils.helper import run_cmd


logger = logging.getLogger(__name__)

try:
    import iptc
except (FileNotFoundError, AttributeError) as err:
    if "pytest" in sys.modules or ENV == 'dev':
        from collections import namedtuple  # hotfix for tests
        iptc = namedtuple('iptc', ['Chain', 'Rule'])
    else:
        logger.error(f'Unable to import iptc due to an error {err}')


ALLOWED_INCOMING_TCP_PORTS = [
    '80',  # filestorage
    '311',  # watchdog https
    '8080',  # http
    '443',  # https
    '53',  # dns
    '3009',  # watchdog http
    '9100'  # node exporter
]

ALLOWED_INCOMING_UDP_PORTS = [
    '53'  # dns
]


def configure_iptables():
    """
    This is the main function used for the initial setup of the firewall rules on the SKALE Node
    host machine
    """
    logger.info('Configuring iptables...')
    if not iptc:
        raise ImportError('Unable to import iptc package')
    Path(IPTABLES_DIR).mkdir(parents=True, exist_ok=True)

    tb = iptc.Table(iptc.Table.FILTER)
    input_chain = iptc.Chain(tb, 'INPUT')

    set_base_policies()
    allow_loopback(input_chain)
    accept_icmp(input_chain)
    allow_conntrack(input_chain)
    allow_base_ports(input_chain)
    drop_all_tcp(input_chain)
    drop_all_udp(input_chain)
    save_iptables_rules_state()


def save_iptables_rules_state():
    res = run_cmd(['iptables-save'])
    plain_rules = res.stdout.decode('utf-8').rstrip()
    with open(IPTABLES_RULES_STATE_FILEPATH, 'w') as state_file:
        state_file.write(plain_rules)


def set_base_policies() -> None:
    """Drop all incoming, allow all outcoming, drop all forwarding"""
    logger.debug('Setting base policies...')
    iptc.easy.set_policy(iptc.Table.FILTER, 'INPUT', 'ACCEPT')
    iptc.easy.set_policy(iptc.Table.FILTER, 'OUTPUT', 'ACCEPT')
    iptc.easy.set_policy(iptc.Table.FILTER, 'FORWARD', 'DROP')


def allow_loopback(chain: iptc.Chain) -> None:
    """Allow local loopback services"""
    logger.debug('Allowing loopback packages...')
    rule = iptc.Rule()
    rule.target = iptc.Target(rule, 'ACCEPT')
    rule.in_interface = 'lo'
    ensure_rule(chain, rule)


def allow_conntrack(chain: iptc.Chain) -> None:
    """Allow conntrack established connections"""
    logger.debug('Allowing conntrack...')
    rule = iptc.Rule()
    rule.target = iptc.Target(rule, 'ACCEPT')
    match = iptc.Match(rule, 'conntrack')
    chain = iptc.Chain(iptc.Table(iptc.Table.FILTER), 'INPUT')
    match.ctstate = 'RELATED,ESTABLISHED'
    rule.add_match(match)
    ensure_rule(chain, rule)


def drop_all_tcp(chain: iptc.Chain) -> None:
    """Drop the rest of tcp connections"""
    logger.debug('Adding drop tcp rule ...')
    r = iptc.Rule()
    t = iptc.Target(r, 'DROP')
    r.target = t
    r.protocol = 'tcp'
    ensure_rule(chain, r)


def drop_all_udp(chain: iptc.Chain) -> None:
    """Drop the rest of udp connections """
    logger.debug('Adding drop udp rule ...')
    r = iptc.Rule()
    t = iptc.Target(r, 'DROP')
    r.target = t
    r.protocol = 'udp'
    ensure_rule(chain, r)


def get_ssh_port(ssh_service_name='ssh'):
    return socket.getservbyname('ssh')


def allow_ssh(chain: iptc.Chain) -> None:
    ssh_port = get_ssh_port()
    accept_incoming(chain, ssh_port, 'tcp')


def allow_base_ports(chain: iptc.Chain) -> None:
    logger.info('Configuring ssh port...')
    allow_ssh(chain)
    logger.info('Configuring incoming tcp port...')
    for port in ALLOWED_INCOMING_TCP_PORTS:
        accept_incoming(chain, port, 'tcp')
    logger.info('Configuring incoming udp port...')
    for port in ALLOWED_INCOMING_UDP_PORTS:
        accept_incoming(chain, port, 'udp')


def accept_incoming(chain, port, protocol) -> None:
    logger.debug('Going to allow %s traffic from %d port', protocol, port)
    rule = iptc.Rule()
    rule.protocol = protocol
    match = iptc.Match(rule, protocol)
    match.dport = port
    t = iptc.Target(rule, 'ACCEPT')
    rule.target = t
    rule.add_match(match)
    ensure_rule(chain, rule, insert=True)


def accept_icmp(chain: iptc.Chain) -> None:
    add_icmp_rule(chain, 'destination-unreachable')
    add_icmp_rule(chain, 'source-quench')
    add_icmp_rule(chain, 'time-exceeded')


def add_icmp_rule(chain: iptc.Chain, icmp_type: str) -> None:
    rule = iptc.Rule()
    rule.protocol = 'icmp'
    match = iptc.Match(rule, 'icmp')
    match.icmp_type = icmp_type
    t = iptc.Target(rule, 'ACCEPT')
    rule.target = t
    rule.add_match(match)
    ensure_rule(chain, rule)


def ensure_rule(chain: iptc.Chain, rule: iptc.Rule, insert=False) -> None:
    if rule not in chain.rules:
        logger.debug(f'Adding rule: {rule_to_dict(rule)}, chain: {chain.name}')
        if insert:
            chain.insert_rule(rule)
        else:
            chain.append_rule(rule)
    else:
        logger.debug(f'Rule already present: {rule_to_dict(rule)}, chain: {chain.name}')


def rule_to_dict(rule):
    return {
        'proto': rule.protocol,
        'src': rule.src,
        'dst': rule.dst,
        'in_interface': rule.in_interface,
        'out': rule.out_interface,
        'target': rule.target.name,
    }
