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
from node_cli.utils.helper import get_ssh_port, read_json, run_cmd

logger = logging.getLogger(__name__)


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
POLICY = 'accept'
POLICY_DROP = 'drop'

# Prefix of the dynamic per-sChain chains managed by skale-admin
# in the same inet/firewall table (skale-<schain>, skale-network-scope, ...)
DYNAMIC_CHAIN_PREFIX = 'skale-'

# sChain base ports are allocated as node_base_port + schain_index * 64
# (PORTS_PER_SCHAIN in skale.py); 128 slots cover every possible allocation
SCHAIN_PORTS_PER_NODE = 128 * 64
SCHAIN_BASE_PORT_ENV = 'SCHAIN_BASE_PORT'
FIREWALL_DEFAULT_DROP_ENV = 'FIREWALL_DEFAULT_DROP'
MIN_SCHAIN_BASE_PORT = 2000
MAX_PORT = 65535

# Without these a drop policy on an inet chain breaks IPv6 neighbor
# discovery and path MTU discovery
ICMPV6_ACCEPT_TYPES = (
    'destination-unreachable',
    'packet-too-big',
    'time-exceeded',
    'parameter-problem',
    'nd-router-advert',
    'nd-neighbor-solicit',
    'nd-neighbor-advert',
)


try:
    import nftables
except (FileNotFoundError, AttributeError, ModuleNotFoundError) as err:
    if 'pytest' in sys.modules or ENV == 'dev':
        from collections import namedtuple  # hotfix for tests

        iptc = namedtuple('nftables', ['Chain', 'Rule'])
    else:
        logger.error(f'Unable to import nftables due to an error {err}')


class NFTablesError(Exception):
    pass


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
        if all(
            val is None for val in (self.first_port, self.last_port, self.protocol, self.icmp_type)
        ):
            raise NFTablesError('Rule has no meaningful fields')


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
        self, chain: str, hook: str, priority: int = CHAIN_PRIORITY, policy: str = POLICY
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
        policy: str = POLICY,
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
            for item in data.get('nftables', []):
                if 'chain' in item and item['chain'].get('name') == chain:
                    return item['chain'].get('policy')
        except Exception as e:
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

    def rule_exists(self, chain: str, new_rule_expr: list[dict]) -> bool:
        existing_rules = self.get_rules(chain)

        for rule in existing_rules:
            expr = rule.get('expr')
            for i, statement in enumerate(expr):
                if 'counter' in statement:
                    expr[i] = {'counter': None}
            rule['counter'] = None
            if expr == new_rule_expr:
                return True
        return False

    def add_drop_rule(self, rule: Rule) -> None:
        expr = []

        if rule.first_port:
            if rule.last_port == rule.first_port:
                expr.append(
                    {
                        'match': {
                            'op': '==',
                            'left': {'payload': {'protocol': 'tcp', 'field': 'dport'}},
                            'right': rule.first_port,
                        }
                    }
                )
            else:
                expr.append(
                    {
                        'match': {
                            'op': '==',
                            'left': {'payload': {'protocol': 'tcp', 'field': 'dport'}},
                            'right': {'range': [rule.first_port, rule.last_port]},
                        }
                    }
                )
        expr.append(
            {
                'match': {
                    'left': {'payload': {'protocol': 'ip', 'field': 'protocol'}},
                    'op': '==',
                    'right': rule.protocol,
                }
            },
        )
        expr.extend([{'counter': None}, {'drop': None}])
        if not self.rule_exists(self.chain, expr):
            cmd = {
                'nftables': [
                    {
                        'add': {
                            'rule': {
                                'family': self.family,
                                'table': self.table,
                                'chain': rule.chain,
                                'expr': expr,
                            }
                        }
                    }
                ]
            }
            self.execute_cmd(cmd)
            logger.info('Added drop rule %s', Rule)

    def remove_drop_rule(self, protocol: str) -> None:
        expr = [
            {
                'match': {
                    'op': '==',
                    'left': {'payload': {'protocol': 'ip', 'field': 'protocol'}},
                    'right': protocol,
                }
            },
            {'counter': None},
            {'drop': None},
        ]

        # Check if the drop rule exists before attempting to remove it
        if self.rule_exists(self.chain, expr):
            cmd = {
                'nftables': [
                    {
                        'delete': {
                            'rule': {
                                'family': self.family,
                                'table': self.table,
                                'chain': self.chain,
                                'expr': expr,
                            }
                        }
                    }
                ]
            }
            self.execute_cmd(cmd)
            logger.info('Removed drop rule for %s', protocol)
        else:
            logger.info('Drop rule does not exist for %s', protocol)

    def add_rule(self, rule: Rule) -> None:
        expr = []

        if rule.protocol in ['tcp', 'udp']:
            if rule.first_port:
                if rule.last_port == rule.first_port:
                    expr.append(
                        {
                            'match': {
                                'op': '==',
                                'left': {'payload': {'protocol': rule.protocol, 'field': 'dport'}},
                                'right': rule.first_port,
                            }
                        }
                    )
                else:
                    expr.append(
                        {
                            'match': {
                                'op': '==',
                                'left': {'payload': {'protocol': rule.protocol, 'field': 'dport'}},
                                'right': {'range': [rule.first_port, rule.last_port]},
                            }
                        }
                    )
        elif rule.protocol in ['icmp', 'icmpv6'] and rule.icmp_type:
            expr.append(
                {
                    'match': {
                        'left': {'payload': {'protocol': rule.protocol, 'field': 'type'}},
                        'op': '==',
                        'right': rule.icmp_type,
                    }
                }
            )

        expr.append({'counter': None})
        expr.append({rule.action: None})

        if not self.rule_exists(rule.chain, expr):
            cmd = {
                'nftables': [
                    {
                        'add': {
                            'rule': {
                                'family': self.family,
                                'table': self.table,
                                'chain': rule.chain,
                                'expr': expr,
                            }
                        }
                    }
                ]
            }
            self.execute_cmd(cmd)
            logger.info(
                'Added new rule to chain %s: %s ports [%s, %s]',
                rule.chain,
                rule.protocol,
                rule.first_port,
                rule.last_port,
            )
        else:
            logger.info(
                'Rule already exists in chain %s: %s ports [%s, %s]',
                rule.chain,
                rule.protocol,
                rule.first_port,
                rule.last_port,
            )

    def remove_rule(self, rule: Rule) -> None:
        expr = []

        if rule.protocol in ['tcp', 'udp']:
            if rule.first_port:
                if rule.last_port == rule.first_port:
                    expr.append(
                        {
                            'match': {
                                'op': '==',
                                'left': {'payload': {'protocol': rule.protocol, 'field': 'dport'}},
                                'right': rule.first_port,
                            }
                        }
                    )
                else:
                    expr.append(
                        {
                            'match': {
                                'op': '==',
                                'left': {'payload': {'protocol': rule.protocol, 'field': 'dport'}},
                                'right': {'range': [rule.first_port, rule.last_port]},
                            }
                        }
                    )
        elif rule.protocol == 'icmp' and rule.icmp_type:
            expr.append(
                {
                    'match': {
                        'left': {'payload': {'protocol': 'icmp', 'field': 'type'}},
                        'op': '==',
                        'right': rule.icmp_type,
                    }
                }
            )

        # Check if the rule exists before attempting to remove it
        if self.rule_exists(rule.chain, expr):
            cmd = {
                'nftables': [
                    {
                        'delete': {
                            'rule': {
                                'family': self.family,
                                'table': self.table,
                                'chain': rule.chain,
                                'expr': expr,
                            }
                        }
                    }
                ]
            }
            self.execute_cmd(cmd)
            logger.info(
                'Removed rule from chain %s: %s ports [%s, %s]',
                rule.chain,
                rule.protocol,
                rule.first_port,
                rule.last_port,
            )
        else:
            logger.info(
                'Rule does not exist in chain %s: %s ports [%s, %s]',
                rule.chain,
                rule.protocol,
                rule.first_port,
                rule.last_port,
            )

    def add_connection_tracking_rule(self, chain: str) -> None:
        expr = [
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

        if not self.rule_exists(chain, expr):
            cmd = {
                'nftables': [
                    {
                        'add': {
                            'rule': {
                                'family': self.family,
                                'table': self.table,
                                'chain': chain,
                                'expr': expr,
                            }
                        }
                    }
                ]
            }
            self.execute_cmd(cmd)
            logger.info('Added connection tracking rule to chain %s', chain)
        else:
            logger.info('Connection tracking rule already exists in chain %s', chain)

    def add_loopback_rule(self, chain) -> None:
        expr = [
            {'match': {'left': {'meta': {'key': 'iifname'}}, 'op': '==', 'right': 'lo'}},
            {'counter': None},
            {'accept': None},
        ]
        if not self.rule_exists(chain, expr):
            json_cmd = {
                'nftables': [
                    {
                        'add': {
                            'rule': {
                                'family': self.family,
                                'table': self.table,
                                'chain': self.chain,
                                'expr': expr,
                            }
                        }
                    }
                ]
            }
            self.execute_cmd(json_cmd)
        else:
            logger.info('Loopback rule already exists in chain %s', chain)

    def get_dynamic_chain_port_ranges(self) -> list[tuple[str, int, int]]:
        """Min/max tcp dport covered by each dynamic skale-admin chain."""
        try:
            rc, output, error = self.nft.cmd(f'list table {self.family} {self.table}')
            if rc != 0:
                if error and 'No such file or directory' in error:
                    return []
                raise NFTablesError(f'Failed to list table {self.table}: {error}')
            data = json.loads(output)
        except NFTablesError:
            raise
        except Exception as e:
            logger.error('Failed to get dynamic chain ranges: %s', e)
            raise NFTablesError(e)

        ports: dict[str, list[int]] = {}
        for item in data.get('nftables', []):
            rule = item.get('rule')
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
        conntrack_expr = [
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
        ssh_expr = [
            {
                'match': {
                    'op': '==',
                    'left': {'payload': {'protocol': 'tcp', 'field': 'dport'}},
                    'right': get_ssh_port(),
                }
            },
            {'counter': None},
            {'accept': None},
        ]
        for name, expr in (('conntrack', conntrack_expr), ('ssh', ssh_expr)):
            if not self.rule_exists(self.chain, expr):
                raise NFTablesError(
                    f'Refusing to set drop policy: {name} accept rule is missing '
                    f'in chain {self.chain}'
                )

    def ensure_default_drop(self, envelope: tuple[int, int]) -> None:
        """Switch the skale chain policy to drop after validating the accepts."""
        self.validate_dynamic_ranges(envelope)
        self.verify_critical_accepts()
        if self.get_chain_policy(self.chain) != POLICY_DROP:
            self.update_chain_policy(chain=self.chain, policy=POLICY_DROP)

    def ensure_default_accept(self) -> None:
        """Rollback path: switch the skale chain policy back to accept."""
        if self.get_chain_policy(self.chain) == POLICY_DROP:
            self.update_chain_policy(chain=self.chain, policy=POLICY)

    def delete_rule_by_handle(self, handle: int) -> None:
        cmd = {
            'nftables': [
                {
                    'delete': {
                        'rule': {
                            'family': self.family,
                            'table': self.table,
                            'chain': self.chain,
                            'handle': handle,
                        }
                    }
                }
            ]
        }
        self.execute_cmd(cmd)

    def remove_stale_envelope_rules(self, envelope: tuple[int, int]) -> None:
        """Remove sChain envelope accepts anchored at a different base port."""
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
                    and right['range'][1] - right['range'][0] == SCHAIN_PORTS_PER_NODE - 1
                    and tuple(right['range']) != envelope
                    and rule.get('handle') is not None
                ):
                    logger.info('Removing stale envelope rule %s', right['range'])
                    self.delete_rule_by_handle(rule['handle'])

    @staticmethod
    def _normalized_expr(expr: list[dict]) -> list[dict]:
        return [{'counter': None} if 'counter' in statement else statement for statement in expr]

    def remove_misordered_udp_drop(self) -> None:
        """Delete the blanket udp drop when it shadows the udp DNS accept.

        Rulesets created before the udp payload fix have the drop above the
        accept; setup re-adds the drop after all accept rules.
        """
        udp_drop = [
            {
                'match': {
                    'left': {'payload': {'protocol': 'ip', 'field': 'protocol'}},
                    'op': '==',
                    'right': 'udp',
                }
            },
            {'counter': None},
            {'drop': None},
        ]
        udp_dns_accept = [
            {
                'match': {
                    'op': '==',
                    'left': {'payload': {'protocol': 'udp', 'field': 'dport'}},
                    'right': ServicePort.DNS,
                }
            },
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

    def apply_user_rules(self) -> None:
        """Load user.conf rules into the live chain.

        The file is included into the saved config, but the live chain is
        managed through the API - without this, rules added to the file would
        apply only after a reboot and would be missing from the live chain
        when the policy flips to drop.
        """
        if not os.path.isfile(NFTABLES_USER_CONFIG_PATH):
            return
        with open(NFTABLES_USER_CONFIG_PATH) as user_config:
            lines = [line.strip() for line in user_config.readlines()]
        lines = [line for line in lines if line and not line.startswith('#')]
        if not lines:
            return
        current_rules = self.get_base_ruleset()
        # insert in reverse to keep the file order at the top of the chain,
        # mirroring the include position in the saved config
        for line in reversed(lines):
            if line in current_rules:
                continue
            rc, output, error = self.nft.cmd(
                f'insert rule {self.family} {self.table} {self.chain} {line}'
            )
            if rc != 0:
                raise NFTablesError(f'Failed to apply user.conf rule "{line}": {error}')
            logger.info('Applied user.conf rule: %s', line)

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

    def setup_firewall(
        self, enable_monitoring: bool = False, defer_default_drop: bool = False
    ) -> None:
        """Setup firewall rules.

        defer_default_drop keeps the accept policy for now - used when the
        envelope base port is not known yet (fresh passive init, where
        skale-admin computes it only after the containers start).
        """

        logger.info('Configuring firewall rules')
        envelope = get_schain_ports_envelope()
        default_drop = firewall_default_drop_enabled() and not defer_default_drop
        try:
            self.create_table_if_not_exists()
            if default_drop:
                # Fail fast, before any rule is touched, if the envelope does
                # not cover the chains skale-admin already created on this
                # node. Skipped on rollback so that a mismatched envelope
                # cannot block restoring the accept policy.
                self.validate_dynamic_ranges(envelope)

            base_chains_config = {'skale': {'hook': 'input', 'policy': 'accept'}}

            for chain, config in base_chains_config.items():
                self.create_chain_if_not_exists(
                    chain=chain, hook=config['hook'], policy=config['policy']
                )

            self.add_connection_tracking_rule(self.chain)

            tcp_ports = [
                get_ssh_port(),
                ServicePort.DNS,
                ServicePort.HTTPS,
                ServicePort.HTTP,
                ServicePort.WATCHDOG_HTTP,
                ServicePort.WATCHDOG_HTTPS,
            ]
            if enable_monitoring:
                tcp_ports.extend([ServicePort.EXPORTER, ServicePort.CADVISOR])
            for port in tcp_ports:
                self.add_rule(Rule(chain=self.chain, protocol='tcp', first_port=port))

            self.remove_misordered_udp_drop()
            self.add_rule(Rule(chain=self.chain, protocol='udp', first_port=ServicePort.DNS))
            self.add_loopback_rule(chain=self.chain)

            icmp_types = ['destination-unreachable', 'source-quench', 'time-exceeded']
            for icmp_type in icmp_types:
                self.add_rule(Rule(chain=self.chain, protocol='icmp', icmp_type=icmp_type))

            for icmpv6_type in ICMPV6_ACCEPT_TYPES:
                self.add_rule(Rule(chain=self.chain, protocol='icmpv6', icmp_type=icmpv6_type))

            # Fine-grained filtering inside the envelope is enforced by the
            # dynamic skale-admin chains that run earlier (priority 0)
            self.remove_stale_envelope_rules(envelope)
            self.add_rule(
                Rule(
                    chain=self.chain,
                    protocol='tcp',
                    first_port=envelope[0],
                    last_port=envelope[1],
                )
            )

            self.add_drop_rule(
                Rule(
                    chain=self.chain,
                    first_port=SGXPort.HTTPS,
                    last_port=SGXPort.ZMQ,
                    protocol='tcp',
                )
            )

            self.add_drop_rule(Rule(chain=self.chain, protocol='udp'))
            logger.info('Making sure legacy chain has default policy %s', POLICY)
            self.update_chain_policy(
                chain=LEGACY_CHAIN, policy=POLICY, family=LEGACY_FAMILY, table=LEGACY_TABLE
            )

            self.apply_user_rules()

            if default_drop:
                self.ensure_default_drop(envelope)
            else:
                self.ensure_default_accept()

        except Exception as e:
            logger.error('Failed to setup firewall: %s', e)
            raise NFTablesError(e)
        logger.info(
            'Firewall rules are configured, default policy: %s',
            POLICY_DROP if default_drop else POLICY,
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
            tcp_ports.append(get_ssh_port())
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


def firewall_default_drop_enabled() -> bool:
    value = os.getenv(FIREWALL_DEFAULT_DROP_ENV, 'True')
    return value.lower() not in ('false', '0', 'no', 'off')


def get_registered_base_port() -> Optional[int]:
    """Base port for the envelope, taken from the node config.

    node_base_port is the port the node was registered with (saved by
    skale-admin at registration and backfilled from the contracts on admin
    restarts). schain_base_port is the fallback for passive and fair nodes,
    where it holds the single hosted chain's base port - a valid anchor too.
    """
    if not os.path.isfile(NODE_CONFIG_PATH):
        return None
    try:
        node_config = read_json(NODE_CONFIG_PATH)
    except Exception as e:
        logger.warning('Failed to read node config: %s', e)
        return None
    base_port = node_config.get('node_base_port') or node_config.get('schain_base_port') or 0
    return base_port if base_port > 0 else None


def get_schain_ports_envelope() -> tuple[int, int]:
    """Range of ports that can be allocated to sChains on this node."""
    env_value = os.getenv(SCHAIN_BASE_PORT_ENV)
    if env_value:
        try:
            base_port = int(env_value)
        except ValueError:
            raise NFTablesError(f'{SCHAIN_BASE_PORT_ENV} must be an integer, got {env_value}')
    else:
        base_port = get_registered_base_port() or DEFAULT_NODE_BASE_PORT
    if not MIN_SCHAIN_BASE_PORT <= base_port <= MAX_PORT - SCHAIN_PORTS_PER_NODE + 1:
        raise NFTablesError(f'Invalid sChain base port {base_port}')
    return base_port, base_port + SCHAIN_PORTS_PER_NODE - 1


def prepare_directories() -> None:
    logger.info('Prepare directories for nftables')
    os.makedirs(NFTABLES_CHAIN_FOLDER_PATH, exist_ok=True)
    create_user_config_path()


def configure_nftables(enable_monitoring: bool = False, defer_default_drop: bool = False) -> None:
    prepare_directories()
    enable_nftables_service()
    nft_mgr = NFTablesManager()
    nft_mgr.setup_firewall(
        enable_monitoring=enable_monitoring, defer_default_drop=defer_default_drop
    )
    ruleset = nft_mgr.get_base_ruleset()
    save_nftables_rules(ruleset)
    remove_legacy_saved_rules()


def enable_nftables_service() -> None:
    logger.info('Enabling nftables services')
    run_cmd(['systemctl', 'enable', 'nftables'])


def save_nftables_base_rules(ruleset: str) -> None:
    ruleset_lines = ruleset.split('\n')
    chain_include_line = f'\tinclude "{NFTABLES_CHAIN_CONFIG_WILDCARD}"'
    user_include_line = f'\t\tinclude "{NFTABLES_USER_CONFIG_PATH}"'
    ruleset_lines.insert(3, user_include_line)
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
