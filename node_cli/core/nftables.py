#
#   -*- coding: utf-8 -*-
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

import json
import logging
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from node_cli.configs import (
    DEFAULT_NODE_BASE_PORT,
    ENV,
    NFTABLES_CHAIN_CONFIG_WILDCARD,
    NFTABLES_CHAIN_FOLDER_PATH,
    NFTABLES_MAIN_CONFIG_PATH,
    NFTABLES_SKALE_BASE_CONFIG_PATH,
    NFTABLES_USER_CONFIG_PATH,
    NODE_CONFIG_PATH,
)
from node_cli.utils.helper import cleanup_dir_content, get_ssh_ports, read_json, run_cmd

logger = logging.getLogger(__name__)

try:
    import nftables
except (FileNotFoundError, AttributeError, ModuleNotFoundError) as err:
    if 'pytest' in sys.modules or ENV == 'dev':
        from collections import namedtuple  # hotfix for tests

        iptc = namedtuple('nftables', ['Chain', 'Rule'])
    else:
        logger.error(f'Unable to import nftables due to an error {err}')


@dataclass
class ServicePort:
    DNS: int = 53
    CADVISOR: int = 9100
    EXPORTER: int = 8080
    WATCHDOG_HTTP: int = 3009
    WATCHDOG_HTTPS: int = 311
    HTTPS: int = 443
    HTTP: int = 80


@dataclass
class SGXPort:
    HTTPS: int = 1026
    TLS: int = 1027
    LOCAL: int = 1028
    HTTP_ONLY: int = 1029
    INFO: int = 1030
    ZMQ: int = 1031


LEGACY_CHAIN = 'INPUT'
LEGACY_FAMILY = 'ip'
LEGACY_TABLE = 'filter'
CHAIN_PRIORITY = 1
HOOK = 'input'
POLICY_ACCEPT = 'accept'
POLICY_DROP = 'drop'

DYNAMIC_CHAIN_PREFIX = 'skale-'

USER_CHAIN = 'skale_user'

# sChain base ports are allocated as node_base_port + schain_index * 64
# (PORTS_PER_SCHAIN in skale.py); 128 slots cover every possible allocation
PORTS_PER_SCHAIN = 64
SCHAIN_PORTS_PER_NODE = 128 * PORTS_PER_SCHAIN
SCHAIN_BASE_PORT_ENV = 'SCHAIN_BASE_PORT'
FIREWALL_DEFAULT_DROP_ENV = 'FIREWALL_DEFAULT_DROP'
MIN_SCHAIN_BASE_PORT = 2000
MAX_PORT = 65535

ICMP_ACCEPT_TYPES = ('destination-unreachable', 'time-exceeded')
ICMPV6_ACCEPT_TYPES = (
    'destination-unreachable',
    'packet-too-big',
    'time-exceeded',
    'parameter-problem',
    'nd-router-advert',
    'nd-neighbor-solicit',
    'nd-neighbor-advert',
)


class NFTablesError(Exception):
    pass


def dport_match(protocol: str, first_port: int, last_port: int) -> dict:
    right = first_port if last_port == first_port else {'range': [first_port, last_port]}
    return {
        'match': {
            'op': '==',
            'left': {'payload': {'protocol': protocol, 'field': 'dport'}},
            'right': right,
        }
    }


def icmp_match(protocol: str, icmp_type: str) -> dict:
    return {
        'match': {
            'left': {'payload': {'protocol': protocol, 'field': 'type'}},
            'op': '==',
            'right': icmp_type,
        }
    }


def ip_protocol_match(protocol: str) -> dict:
    return {
        'match': {
            'left': {'payload': {'protocol': 'ip', 'field': 'protocol'}},
            'op': '==',
            'right': protocol,
        }
    }


def conntrack_accept_expr() -> list[dict]:
    return [
        {
            'match': {
                'left': {'ct': {'key': 'state'}},
                'op': 'in',
                'right': ['established', 'related'],
            }
        },
        {'counter': None},
        {'accept': None},
    ]


def loopback_accept_expr() -> list[dict]:
    return [
        {'match': {'left': {'meta': {'key': 'iifname'}}, 'op': '==', 'right': 'lo'}},
        {'counter': None},
        {'accept': None},
    ]


@dataclass
class Rule:
    chain: str
    protocol: str
    first_port: Optional[int] = None
    last_port: Optional[int] = None
    icmp_type: Optional[str] = None
    action: str = 'accept'

    def __post_init__(self):
        if self.first_port is not None and self.last_port is None:
            self.last_port = self.first_port
        if self.protocol in ('icmp', 'icmpv6') and not self.icmp_type:
            raise NFTablesError(f'{self.protocol} rule requires icmp_type')

    def to_expr(self) -> list[dict]:
        matches = []
        if self.protocol in ('tcp', 'udp') and self.first_port:
            matches.append(dport_match(self.protocol, self.first_port, self.last_port))
        elif self.protocol in ('icmp', 'icmpv6'):
            matches.append(icmp_match(self.protocol, self.icmp_type))
        return [*matches, {'counter': None}, {self.action: None}]


class NFTablesManager:
    def __init__(self, family: str = 'inet', table: str = 'firewall', chain: str = 'skale') -> None:
        self.nft = nftables.Nftables()
        self.nft.set_json_output(True)
        self.nft.set_stateless_output(True)
        self.family = family
        self.table = table
        self.chain = chain

    def execute_cmd(self, json_cmd: dict) -> None:
        logger.debug('Executing nft cmd %s', json_cmd)
        try:
            rc, output, error = self.nft.json_cmd(json_cmd)
            if rc != 0:
                raise NFTablesError(f'Command failed: {error}')
            return output
        except Exception as e:
            logger.error('Failed to execute command: %s', e)
            raise NFTablesError(e)

    def get_chains(self, family: Optional[str] = None) -> list[str]:
        family = family or self.family
        try:
            rc, output, error = self.nft.cmd(f'list chains {family}')
            if rc != 0:
                if 'No such file or directory' in error:
                    return []
                raise NFTablesError(f'Failed to list chains: {error}')

            chains = json.loads(output)
            return [item['chain']['name'] for item in chains.get('nftables', []) if 'chain' in item]
        except Exception as e:
            logger.error('Failed to get chains: %s', e)
            return []

    def flush(self) -> None:
        self.nft.cmd('flush ruleset')

    def chain_exists(self, chain: str, family: Optional[str] = None) -> bool:
        family = family or self.family
        return chain in self.get_chains(family=family)

    def create_chain_if_not_exists(
        self, chain: str, hook: str, priority: int = CHAIN_PRIORITY, policy: str = POLICY_ACCEPT
    ) -> None:
        if not self.chain_exists(chain):
            cmd = {
                'nftables': [
                    {
                        'add': {
                            'chain': {
                                'family': self.family,
                                'table': self.table,
                                'name': chain,
                                'type': 'filter',
                                'hook': hook,
                                'prio': priority,
                                'policy': policy,
                            }
                        }
                    }
                ]
            }
            self.execute_cmd(cmd)
            logger.info('Created new chain: %s %s', chain, cmd)
        else:
            logger.info('Chain already exists: %s', chain)

    def update_chain_policy(
        self,
        chain: str,
        policy: str = POLICY_ACCEPT,
        family: Optional[str] = None,
        table: Optional[str] = None,
    ) -> None:
        """Update specified chain if it exists. Otherwise do nothing."""
        family = family or self.family
        table = table or self.table
        if self.chain_exists(chain, family=family):
            cmd = f'add chain {family} {table} {chain} {{ policy {policy} ; }}'
            rc, output, error = self.nft.cmd(cmd)
            if rc != 0:
                raise NFTablesError(f'Failed to set policy {policy} on {chain}: {error}')
            logger.info('Updated chain policy: %s %s', chain, policy)
        else:
            logger.info('Chain %s does not exist', chain)

    def get_chain_policy(self, chain: str) -> Optional[str]:
        """Return the policy of a chain in the managed table or None."""
        try:
            rc, output, error = self.nft.cmd(f'list chain {self.family} {self.table} {chain}')
            if rc != 0:
                return None
            data = json.loads(output)
            if not isinstance(data, dict):
                return None
            for item in data.get('nftables', []):
                if not isinstance(item, dict):
                    continue
                chain_data = item.get('chain')
                if isinstance(chain_data, dict) and chain_data.get('name') == chain:
                    return chain_data.get('policy')
        except (TypeError, ValueError) as e:
            logger.error('Failed to get policy of chain %s: %s', chain, e)
        return None

    def table_exists(self) -> bool:
        try:
            rc, output, error = self.nft.cmd(f'list table {self.family} {self.table}')
            return rc == 0
        except Exception:
            return False

    def create_table_if_not_exists(self) -> None:
        """Create table only if it doesn't exist."""
        if not self.table_exists():
            cmd = {'nftables': [{'add': {'table': {'family': self.family, 'name': self.table}}}]}
            self.execute_cmd(cmd)
            logger.info('Created new table: %s', self.table)
        else:
            logger.info('Table already exists: %s', self.table)

    def get_rules(self, chain: str) -> list[dict]:
        """Get existing rules for a chain."""
        try:
            cmd = f'list chain {self.family} {self.table} {chain}'
            rc, output, error = self.nft.cmd(cmd)
            if rc != 0:
                if 'No such file or directory' in error:
                    return []
                raise NFTablesError(f'Failed to list rules: {error}')

            rules = json.loads(output)
            return [item['rule'] for item in rules.get('nftables', []) if 'rule' in item]
        except Exception as e:
            logger.error('Failed to get rules: %s', e)
            return []

    @staticmethod
    def _normalized_expr(expr: list[dict]) -> list[dict]:
        return [{'counter': None} if 'counter' in statement else statement for statement in expr]

    def rule_exists(self, chain: str, new_rule_expr: list[dict]) -> bool:
        target = self._normalized_expr(new_rule_expr)
        return any(
            self._normalized_expr(rule.get('expr', [])) == target for rule in self.get_rules(chain)
        )

    def _execute_rule_with_op(
        self,
        op: str,
        chain: str,
        expr: Optional[list[dict]] = None,
        handle: Optional[int] = None,
    ) -> None:
        rule: dict = {'family': self.family, 'table': self.table, 'chain': chain}
        if expr is not None:
            rule['expr'] = expr
        if handle is not None:
            rule['handle'] = handle
        self.execute_cmd({'nftables': [{op: {'rule': rule}}]})

    def _ensure_rule(
        self, chain: str, expr: list[dict], op: str = 'add', label: str = 'rule'
    ) -> None:
        if self.rule_exists(chain, expr):
            logger.info('%s already exists in chain %s', label, chain)
            return
        self._execute_rule_with_op(op, chain, expr=expr)
        logger.info('Added %s to chain %s', label, chain)

    def _find_rule_handle(self, chain: str, expr: list[dict]) -> Optional[int]:
        target = self._normalized_expr(expr)
        for rule in self.get_rules(chain):
            if (
                self._normalized_expr(rule.get('expr', [])) == target
                and rule.get('handle') is not None
            ):
                return rule['handle']
        return None

    def _remove_rule_by_expr(self, chain: str, expr: list[dict]) -> bool:
        handle = self._find_rule_handle(chain, expr)
        if handle is None:
            return False
        self.delete_rule_by_handle(handle, chain=chain)
        return True

    @staticmethod
    def _protocol_drop_expr(rule: Rule) -> list[dict]:
        matches = []
        if rule.first_port:
            matches.append(dport_match('tcp', rule.first_port, rule.last_port))
        matches.append(ip_protocol_match(rule.protocol))
        return [*matches, {'counter': None}, {'drop': None}]

    def add_drop_rule(self, rule: Rule) -> None:
        self._ensure_rule(
            rule.chain,
            self._protocol_drop_expr(rule),
            label=f'{rule.protocol} drop rule',
        )

    def remove_drop_rule(self, protocol: str) -> None:
        expr = [ip_protocol_match(protocol), {'counter': None}, {'drop': None}]
        if self._remove_rule_by_expr(self.chain, expr):
            logger.info('Removed drop rule for %s', protocol)
        else:
            logger.info('Drop rule does not exist for %s', protocol)

    def add_rule(self, rule: Rule) -> None:
        self._ensure_rule(
            rule.chain,
            rule.to_expr(),
            label=f'{rule.protocol} {rule.icmp_type or rule.first_port} {rule.action} rule',
        )

    def remove_rule(self, rule: Rule) -> None:
        if self._remove_rule_by_expr(rule.chain, rule.to_expr()):
            logger.info('Removed %s rule for %s', rule.protocol, rule.first_port)
        else:
            logger.info('No %s rule for %s to remove', rule.protocol, rule.first_port)

    def _table_listing(self) -> dict:
        """Parsed json listing of the managed table; empty when absent."""
        rc, output, error = self.nft.cmd(f'list table {self.family} {self.table}')
        if rc != 0:
            if error and 'No such file or directory' in error:
                return {}
            raise NFTablesError(f'Failed to list table {self.table}: {error}')
        try:
            data = json.loads(output)
        except (TypeError, ValueError) as err:
            raise NFTablesError(f'Failed to parse table {self.table} listing: {err}') from err
        if not isinstance(data, dict):
            raise NFTablesError(f'Malformed table {self.table} listing')
        return data

    def _table_chain_names(self) -> list[str]:
        return [
            item['chain']['name']
            for item in self._table_listing().get('nftables', [])
            if isinstance(item, dict) and isinstance(item.get('chain'), dict)
        ]

    def get_dynamic_chain_port_ranges(self) -> list[tuple[str, int, int]]:
        """Min/max tcp dport covered by each dynamic skale-admin chain."""
        data = self._table_listing()

        ports: dict[str, list[int]] = {}
        for item in data.get('nftables', []):
            rule = item.get('rule') if isinstance(item, dict) else None
            if not rule or not rule.get('chain', '').startswith(DYNAMIC_CHAIN_PREFIX):
                continue
            for statement in rule.get('expr', []):
                match = statement.get('match', {})
                if match.get('left', {}).get('payload', {}).get('field') != 'dport':
                    continue
                right = match.get('right')
                chain_ports = ports.setdefault(rule['chain'], [])
                if isinstance(right, dict) and 'range' in right:
                    chain_ports.extend(right['range'])
                elif isinstance(right, int):
                    chain_ports.append(right)
        return [(chain, min(values), max(values)) for chain, values in ports.items() if values]

    def validate_dynamic_ranges(self, envelope: tuple[int, int]) -> None:
        """Ensure ports of every dynamic skale-admin chain fit into the envelope."""
        for chain, first_port, last_port in self.get_dynamic_chain_port_ranges():
            if first_port < envelope[0] or last_port > envelope[1]:
                raise NFTablesError(
                    f'Ports {first_port}-{last_port} of dynamic chain {chain} are outside '
                    f'of the allowed sChain ports range {envelope[0]}-{envelope[1]}. '
                    f'Set {SCHAIN_BASE_PORT_ENV} env variable to the base port the node '
                    'was registered with and rerun the command'
                )

    def verify_critical_accepts(self) -> None:
        """Ensure lockout-critical accept rules are in place before setting drop policy."""
        accepts = [('conntrack', conntrack_accept_expr())]
        accepts.extend(
            (f'ssh port {port}', Rule(chain=self.chain, protocol='tcp', first_port=port).to_expr())
            for port in get_ssh_ports()
        )
        for name, expr in accepts:
            if not self.rule_exists(self.chain, expr):
                raise NFTablesError(
                    f'Refusing to set drop policy: {name} accept rule is missing '
                    f'in chain {self.chain}'
                )

    def ensure_default_drop(self) -> None:
        """Switch the skale chain policy to drop after verifying the accepts."""
        self.verify_critical_accepts()
        if self.get_chain_policy(self.chain) != POLICY_DROP:
            self.update_chain_policy(chain=self.chain, policy=POLICY_DROP)

    def ensure_default_accept(self) -> None:
        if self.get_chain_policy(self.chain) != POLICY_ACCEPT:
            self.update_chain_policy(chain=self.chain, policy=POLICY_ACCEPT)

    def delete_rule_by_handle(self, handle: int, chain: Optional[str] = None) -> None:
        self._execute_rule_with_op('delete', chain or self.chain, handle=handle)

    def remove_stale_envelope_rules(self, envelope: tuple[int, int]) -> None:
        """Remove sChain envelope accepts anchored at a different base port."""
        envelope_spans = (SCHAIN_PORTS_PER_NODE - 1, PORTS_PER_SCHAIN - 1)
        for rule in self.get_rules(self.chain):
            expr = rule.get('expr', [])
            if {'accept': None} not in expr:
                continue
            for statement in expr:
                match = statement.get('match', {})
                right = match.get('right')
                if (
                    match.get('left', {}).get('payload', {}).get('field') == 'dport'
                    and isinstance(right, dict)
                    and 'range' in right
                    and right['range'][1] - right['range'][0] in envelope_spans
                    and tuple(right['range']) != envelope
                    and rule.get('handle') is not None
                ):
                    logger.info('Removing stale envelope rule %s', right['range'])
                    self.delete_rule_by_handle(rule['handle'])

    def remove_misordered_udp_drop(self) -> None:
        """Delete the blanket udp drop when it shadows the udp DNS accept."""
        udp_drop = [ip_protocol_match('udp'), {'counter': None}, {'drop': None}]
        udp_dns_accept = [
            dport_match('udp', ServicePort.DNS, ServicePort.DNS),
            {'counter': None},
            {'accept': None},
        ]
        drop_handle, drop_index, accept_index = None, None, None
        for index, rule in enumerate(self.get_rules(self.chain)):
            expr = self._normalized_expr(rule.get('expr', []))
            if expr == udp_drop:
                drop_handle, drop_index = rule.get('handle'), index
            elif expr == udp_dns_accept:
                accept_index = index
        if drop_handle is not None and (accept_index is None or drop_index < accept_index):
            logger.info('Removing misordered udp drop rule')
            self.delete_rule_by_handle(drop_handle)

    def remove_source_quench_rule(self) -> None:
        """Remove the legacy icmp source-quench accept (deprecated by RFC 6633)."""
        expr = [icmp_match('icmp', 'source-quench'), {'counter': None}, {'accept': None}]
        if self._remove_rule_by_expr(self.chain, expr):
            logger.info('Removed legacy source-quench rule')

    def create_user_chain_if_not_exists(self) -> None:
        """Create the regular chain holding user.conf rules."""
        if not self.chain_exists(USER_CHAIN):
            cmd = {
                'nftables': [
                    {
                        'add': {
                            'chain': {
                                'family': self.family,
                                'table': self.table,
                                'name': USER_CHAIN,
                            }
                        }
                    }
                ]
            }
            self.execute_cmd(cmd)
            logger.info('Created user rules chain %s', USER_CHAIN)

    def ensure_user_chain_jump(self) -> None:
        expr = [{'jump': {'target': USER_CHAIN}}]
        self._ensure_rule(self.chain, expr, op='insert', label='user chain jump')

    def apply_user_rules(self) -> None:
        """Reload user.conf into the live user rules chain."""
        content = ''
        if os.path.isfile(NFTABLES_USER_CONFIG_PATH):
            with open(NFTABLES_USER_CONFIG_PATH) as user_config:
                content = user_config.read()
        commands = (
            f'flush chain {self.family} {self.table} {USER_CHAIN}\n'
            f'table {self.family} {self.table} {{\n'
            f'chain {USER_CHAIN} {{\n'
            f'{content}\n'
            f'}}\n'
            f'}}'
        )
        rc, output, error = self.nft.cmd(commands)
        if rc != 0:
            raise NFTablesError(f'Failed to apply user.conf rules: {error}')

    def remove_user_rules_from_main_chain(self) -> None:
        """Remove user.conf rules that older saved configs loaded into the
        skale chain directly.
        """
        user_exprs = [
            self._normalized_expr(rule.get('expr', [])) for rule in self.get_rules(USER_CHAIN)
        ]
        if not user_exprs:
            return
        for rule in self.get_rules(self.chain):
            expr = self._normalized_expr(rule.get('expr', []))
            if expr in user_exprs and rule.get('handle') is not None:
                logger.info('Moving user rule out of the main chain')
                self.delete_rule_by_handle(rule['handle'])

    def get_base_ruleset(self) -> str:
        self.nft.set_json_output(False)
        try:
            cmd = f'list chain {self.family} {self.table} {self.chain}'
            rc, output, error = self.nft.cmd(cmd)
            if rc != 0:
                raise NFTablesError(f'Failed to get ruleset: {error}')
            return output
        finally:
            self.nft.set_json_output(True)

    def _setup_user_chain(self) -> None:
        self.create_user_chain_if_not_exists()
        self.ensure_user_chain_jump()
        self.apply_user_rules()
        self.remove_user_rules_from_main_chain()

    def remove_monitoring_accepts(self) -> None:
        """Remove every legacy monitoring accept from the managed base chain."""
        ssh_ports = get_ssh_ports()
        monitoring_exprs = [
            Rule(chain=self.chain, protocol='tcp', first_port=port).to_expr()
            for port in (ServicePort.EXPORTER, ServicePort.CADVISOR)
            if port not in ssh_ports
        ]
        for rule in self.get_rules(self.chain):
            if (
                self._normalized_expr(rule.get('expr', [])) in monitoring_exprs
                and rule.get('handle') is not None
            ):
                self.delete_rule_by_handle(rule['handle'])

    def _add_service_accepts(self) -> None:
        self._ensure_rule(self.chain, conntrack_accept_expr(), label='connection tracking rule')
        tcp_ports = [
            *get_ssh_ports(),
            ServicePort.DNS,
            ServicePort.HTTPS,
            ServicePort.HTTP,
            ServicePort.WATCHDOG_HTTP,
            ServicePort.WATCHDOG_HTTPS,
        ]
        for port in tcp_ports:
            self.add_rule(Rule(chain=self.chain, protocol='tcp', first_port=port))
        self.remove_misordered_udp_drop()
        self.add_rule(Rule(chain=self.chain, protocol='udp', first_port=ServicePort.DNS))
        self._ensure_rule(self.chain, loopback_accept_expr(), label='loopback rule')

    def _add_icmp_accepts(self) -> None:
        self.remove_source_quench_rule()
        for icmp_type in ICMP_ACCEPT_TYPES:
            self.add_rule(Rule(chain=self.chain, protocol='icmp', icmp_type=icmp_type))
        for icmpv6_type in ICMPV6_ACCEPT_TYPES:
            self.add_rule(Rule(chain=self.chain, protocol='icmpv6', icmp_type=icmpv6_type))

    def _ensure_envelope(self, envelope: tuple[int, int]) -> None:
        # Fine-grained filtering inside the envelope is enforced by the
        # dynamic skale-admin chains that run earlier (priority 0)
        self.remove_stale_envelope_rules(envelope)
        self.add_rule(
            Rule(chain=self.chain, protocol='tcp', first_port=envelope[0], last_port=envelope[1])
        )

    def _add_drop_rules(self) -> None:
        self.add_drop_rule(
            Rule(chain=self.chain, protocol='tcp', first_port=SGXPort.HTTPS, last_port=SGXPort.ZMQ)
        )
        self.add_drop_rule(Rule(chain=self.chain, protocol='udp'))

    def setup_firewall(self, keep_accept_policy: bool = False) -> None:
        """Setup firewall rules."""

        logger.info('Configuring firewall rules')
        default_drop = firewall_default_drop_enabled() and not keep_accept_policy
        try:
            self.create_table_if_not_exists()
            self.create_chain_if_not_exists(chain=self.chain, hook=HOOK, policy=POLICY_ACCEPT)
            if not default_drop:
                # rollback must not be blocked by any later failing step,
                # including an invalid envelope configuration
                self.ensure_default_accept()

            envelope = get_schain_ports_envelope()
            if default_drop:
                # fail fast, before any rule is touched
                self.validate_dynamic_ranges(envelope)

            self._setup_user_chain()
            self.remove_monitoring_accepts()
            self._add_service_accepts()
            self._add_icmp_accepts()
            self._ensure_envelope(envelope)
            self._add_drop_rules()

            logger.info('Making sure legacy chain has default policy %s', POLICY_ACCEPT)
            self.update_chain_policy(
                chain=LEGACY_CHAIN, policy=POLICY_ACCEPT, family=LEGACY_FAMILY, table=LEGACY_TABLE
            )

            if default_drop:
                self.ensure_default_drop()

        except Exception as e:
            logger.error('Failed to setup firewall: %s', e)
            raise NFTablesError(e)
        logger.info(
            'Firewall rules are configured, default policy: %s',
            POLICY_DROP if default_drop else POLICY_ACCEPT,
        )

    def cleanup_legacy_rules(self, ssh: bool = False, dns: bool = False) -> None:
        """Cleans up all node-cli generated rules."""
        self.remove_drop_rule('tcp')
        self.remove_drop_rule('udp')
        tcp_ports = [
            ServicePort.HTTPS,
            ServicePort.WATCHDOG_HTTP,
            ServicePort.WATCHDOG_HTTPS,
            ServicePort.EXPORTER,
            ServicePort.CADVISOR,
            ServicePort.DNS,  # tcp is redundant, making sure it's removed
        ]
        if ssh:
            tcp_ports.extend(get_ssh_ports())
        for port in tcp_ports:
            self.remove_rule(Rule(chain=self.chain, protocol='tcp', first_port=port))
        if dns:
            self.remove_rule(Rule(chain=self.chain, protocol='udp', first_port=ServicePort.DNS))

    def flush_chain(self, chain: str) -> None:
        """Remove all rules from a specific chain."""
        json_cmd = {
            'nftables': [
                {'flush': {'chain': {'family': self.family, 'table': self.table, 'name': chain}}}
            ]
        }

        try:
            rc, output, error = self.nft.json_cmd(json_cmd)
            if rc != 0:
                raise NFTablesError(f'Failed to flush chain: {error}')
        except Exception as e:
            logger.error(f'Failed to flush chain: {str(e)}')
            raise NFTablesError('Flushing chain errored')

    def delete_chain(self, chain: str) -> None:
        chain_spec = {'family': self.family, 'table': self.table, 'name': chain}
        self.execute_cmd(
            {'nftables': [{'flush': {'chain': chain_spec}}, {'delete': {'chain': chain_spec}}]}
        )
        logger.info('Deleted chain %s', chain)

    def _critical_accept_exprs(self) -> list[list[dict]]:
        """Rules that keep the node reachable: conntrack, loopback, ssh, DNS."""
        exprs = [conntrack_accept_expr(), loopback_accept_expr()]
        try:
            ssh_ports = get_ssh_ports()
        except (RuntimeError, ValueError):
            # the policy is accept during cleanup, so reachability is safe
            # even when ssh detection is impossible
            ssh_ports = []
        for port in (*ssh_ports, ServicePort.DNS):
            exprs.append(Rule(chain=self.chain, protocol='tcp', first_port=port).to_expr())
        exprs.append(Rule(chain=self.chain, protocol='udp', first_port=ServicePort.DNS).to_expr())
        return exprs

    def cleanup_firewall(self) -> None:
        """Reset the firewall to a minimal state that keeps the node reachable.

        Restores the accept policy, removes the user and dynamic chains and
        every rule except the critical accepts: conntrack, loopback, ssh
        and DNS.
        """
        self.ensure_default_accept()
        self._remove_rule_by_expr(self.chain, [{'jump': {'target': USER_CHAIN}}])
        for chain in self._table_chain_names():
            if chain == USER_CHAIN or chain.startswith(DYNAMIC_CHAIN_PREFIX):
                self.delete_chain(chain)
        keep = [self._normalized_expr(expr) for expr in self._critical_accept_exprs()]
        for rule in self.get_rules(self.chain):
            if (
                self._normalized_expr(rule.get('expr', [])) not in keep
                and rule.get('handle') is not None
            ):
                self.delete_rule_by_handle(rule['handle'])


def firewall_default_drop_enabled() -> bool:
    value = os.getenv(FIREWALL_DEFAULT_DROP_ENV, 'True')
    return value.lower() not in ('false', '0', 'no', 'off')


def get_registered_base_port() -> Optional[tuple[int, int]]:
    """Base port and envelope size from the node config."""
    if not os.path.isfile(NODE_CONFIG_PATH):
        return None
    try:
        node_config = read_json(NODE_CONFIG_PATH)
    except (OSError, ValueError) as e:
        logger.warning('Failed to read node config: %s', e)
        return None
    if not isinstance(node_config, dict):
        logger.warning('Node config is malformed')
        return None
    for key, size in (
        ('node_base_port', SCHAIN_PORTS_PER_NODE),
        ('schain_base_port', PORTS_PER_SCHAIN),
    ):
        value = node_config.get(key)
        if isinstance(value, int) and not isinstance(value, bool) and value > 0:
            return value, size
    return None


def get_schain_ports_envelope() -> tuple[int, int]:
    """Range of ports that can be allocated to sChains on this node."""
    env_value = os.getenv(SCHAIN_BASE_PORT_ENV)
    if env_value:
        try:
            base_port, size = int(env_value), SCHAIN_PORTS_PER_NODE
        except ValueError:
            raise NFTablesError(f'{SCHAIN_BASE_PORT_ENV} must be an integer, got {env_value}')
    else:
        base_port, size = get_registered_base_port() or (
            DEFAULT_NODE_BASE_PORT,
            SCHAIN_PORTS_PER_NODE,
        )
    if base_port < MIN_SCHAIN_BASE_PORT or base_port + size - 1 > MAX_PORT:
        raise NFTablesError(f'Invalid sChain base port {base_port}')
    return base_port, base_port + size - 1


def prepare_directories() -> None:
    logger.info('Prepare directories for nftables')
    os.makedirs(NFTABLES_CHAIN_FOLDER_PATH, exist_ok=True)
    create_user_config_path()


def configure_nftables(keep_accept_policy: bool = False) -> None:
    prepare_directories()
    enable_nftables_service()
    nft_mgr = NFTablesManager()
    nft_mgr.setup_firewall(keep_accept_policy=keep_accept_policy)
    ruleset = nft_mgr.get_base_ruleset()
    save_nftables_rules(ruleset)
    remove_legacy_saved_rules()


def cleanup_nftables() -> None:
    """Reset the firewall after node cleanup and persist the minimal state."""
    logger.info('Cleaning up firewall rules')
    nft_mgr = NFTablesManager()
    ruleset = ''
    if nft_mgr.table_exists() and nft_mgr.chain_exists(nft_mgr.chain):
        nft_mgr.cleanup_firewall()
        ruleset = nft_mgr.get_base_ruleset()
    if os.path.isdir(NFTABLES_CHAIN_FOLDER_PATH):
        cleanup_dir_content(NFTABLES_CHAIN_FOLDER_PATH)
    if os.path.isdir(os.path.dirname(NFTABLES_SKALE_BASE_CONFIG_PATH)):
        # a plain snapshot with no includes - reboot restores the same
        # minimal ruleset
        with open(NFTABLES_SKALE_BASE_CONFIG_PATH, 'w') as base_config:
            base_config.write(ruleset)


def enable_nftables_service() -> None:
    logger.info('Enabling nftables services')
    run_cmd(['systemctl', 'enable', 'nftables'])


def save_nftables_base_rules(ruleset: str) -> None:
    ruleset_lines = ruleset.split('\n')
    chain_include_line = f'\tinclude "{NFTABLES_CHAIN_CONFIG_WILDCARD}"'
    user_chain_lines = [
        f'\tchain {USER_CHAIN} {{',
        f'\t\tinclude "{NFTABLES_USER_CONFIG_PATH}"',
        '\t}',
    ]
    ruleset_lines[1:1] = user_chain_lines
    ruleset_lines.insert(-2, chain_include_line)
    with open(NFTABLES_SKALE_BASE_CONFIG_PATH, 'w') as f:
        f.write('\n'.join(ruleset_lines))
    logger.info('Rules saved successfully to %s', NFTABLES_SKALE_BASE_CONFIG_PATH)


def create_user_config_path() -> None:
    Path(NFTABLES_USER_CONFIG_PATH).touch(exist_ok=True)


def update_main_nftables_config() -> None:
    logger.info('Updating main nftables rules')
    content = f'#!/usr/sbin/nft -f\nflush ruleset\ninclude "{NFTABLES_SKALE_BASE_CONFIG_PATH}";'
    with open(NFTABLES_MAIN_CONFIG_PATH, 'w') as f:
        f.write(content)


def save_nftables_rules(ruleset: str) -> None:
    logger.info('Saving nftables rules')
    save_nftables_base_rules(ruleset=ruleset)
    update_main_nftables_config()


def remove_legacy_saved_rules() -> None:
    logger.info('Removing saved on disk legacy rules')
    rules_files = ['/etc/iptables/rules.v4', '/etc/iptables/rules.v6']
    backup_files = ['/etc/iptables/.rules.v4', '/etc/iptables/.rules.v6']
    for rules_filepath, backup_filepath in zip(rules_files, backup_files):
        if os.path.isfile(rules_filepath):
            shutil.move(rules_filepath, backup_filepath)
