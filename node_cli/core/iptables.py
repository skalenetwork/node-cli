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
from pathlib import Path
from node_cli.configs import IPTABLES_DIR


logger = logging.getLogger(__name__)

try:
    import iptc
except (FileNotFoundError, AttributeError):
    logger.warning('Unable to import iptc')
    iptc = None


ALLOWED_INCOMING_TCP_PORTS = [
    '22',  # ssh
    '8080',  # http
    '443',  # https
    '53',  # dns
    '3009',  # watchdog
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
        raise Exception('Unable to import iptc package')
    Path(IPTABLES_DIR).mkdir(parents=True, exist_ok=True)

    tb = iptc.Table(iptc.Table.FILTER)
    input_chain = iptc.Chain(tb, 'INPUT')

    set_base_policies()
    allow_loopback(input_chain)
    allow_base_ports(input_chain)
    drop_all_input(input_chain)
    accept_icmp(input_chain)
    allow_conntrack(input_chain)


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
    chain.insert_rule(rule)


def allow_conntrack(chain: iptc.Chain) -> None:
    """Allow conntrack established connections"""
    logger.debug('Allowing conntrack...')
    rule = iptc.Rule()
    rule.protocol = "tcp"
    rule.target = iptc.Target(rule, "ACCEPT")
    match = iptc.Match(rule, "conntrack")
    chain = iptc.Chain(iptc.Table(iptc.Table.FILTER), "INPUT")
    match.ctstate = "RELATED,ESTABLISHED"
    rule.add_match(match)
    chain.insert_rule(rule)


def drop_all_input(chain: iptc.Chain) -> None:
    """Drop all input connections by default (append in the end)"""
    logger.debug('Droping all input connections except specified...')
    r = iptc.Rule()
    t = iptc.Target(r, 'DROP')
    r.target = t
    chain.append_rule(r)


def allow_base_ports(chain: iptc.Chain) -> None:
    logger.debug('Allowing base ports...')
    for port in ALLOWED_INCOMING_TCP_PORTS:
        accept_incoming(chain, port, 'tcp')
    for port in ALLOWED_INCOMING_UDP_PORTS:
        accept_incoming(chain, port, 'udp')


def accept_incoming(chain, port, protocol) -> None:
    rule = iptc.Rule()
    rule.protocol = protocol
    match = iptc.Match(rule, protocol)
    match.dport = port
    t = iptc.Target(rule, 'ACCEPT')
    rule.target = t
    rule.add_match(match)
    safe_add_rule(chain, rule)


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
    safe_add_rule(chain, rule)


def safe_add_rule(chain: iptc.Chain, rule: iptc.Rule) -> None:
    if rule not in chain.rules:
        logger.debug(f'Adding rule: {rule_to_dict(rule)}, chain: {chain.name}')
        chain.insert_rule(rule)
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
