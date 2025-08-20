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
    ENV,
    NFTABLES_CHAIN_CONFIG_WILDCARD,
    NFTABLES_CHAIN_FOLDER_PATH,
    NFTABLES_MAIN_CONFIG_PATH,
    NFTABLES_SKALE_BASE_CONFIG_PATH,
    NFTABLES_USER_CONFIG_PATH,
)
from node_cli.utils.helper import get_ssh_port, run_cmd

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
            cmd = [
                'nft',
                'add',
                'chain',
                family,
                table,
                chain,
                '{',
                'policy',
                POLICY,
                ';',
                '}',
            ]
            run_cmd(cmd)
            logger.info('Updated chain policy: %s %s', chain, policy)
        else:
            logger.info('Chain %s does not exist', chain)

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

    def get_base_ruleset(self) -> str:
        self.nft.set_json_output(False)
        output = ''
        try:
            cmd = f'list chain {self.family} {self.table} {self.chain}'
            rc, output, error = self.nft.cmd(cmd)
            if rc != 0:
                raise NFTablesError(f'Failed to get ruleset: {error}')
            return output
        finally:
            self.nft.set_json_output(True)

        return output

    def setup_firewall(self, enable_monitoring: bool = False) -> None:
        """Setup firewall rules."""

        logger.info('Configuring firewall rules')
        try:
            self.create_table_if_not_exists()

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

            self.add_rule(Rule(chain=self.chain, protocol='udp', first_port=ServicePort.DNS))
            self.add_loopback_rule(chain=self.chain)

            icmp_types = ['destination-unreachable', 'source-quench', 'time-exceeded']
            for icmp_type in icmp_types:
                self.add_rule(Rule(chain=self.chain, protocol='icmp', icmp_type=icmp_type))

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

        except Exception as e:
            logger.error('Failed to setup firewall: %s', e)
            raise NFTablesError(e)
        logger.info('Firewall rules are configured')

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


def prepare_directories() -> None:
    logger.info('Prepare directories for nftables')
    os.makedirs(NFTABLES_CHAIN_FOLDER_PATH, exist_ok=True)
    create_user_config_path()


def configure_nftables(enable_monitoring: bool = False) -> None:
    prepare_directories()
    enable_nftables_service()
    nft_mgr = NFTablesManager()
    nft_mgr.setup_firewall(enable_monitoring=enable_monitoring)
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
