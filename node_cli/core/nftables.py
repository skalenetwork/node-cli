import json
import logging
import sys
from typing import Optional
from dataclasses import dataclass

from node_cli.configs import ENV
from node_cli.utils.helper import get_ssh_port

logger = logging.getLogger(__name__)


try:
    import nftables
except (FileNotFoundError, AttributeError, ModuleNotFoundError) as err:
    if "pytest" in sys.modules or ENV == 'dev':
        from collections import namedtuple  # hotfix for tests
        iptc = namedtuple('nftables', ['Chain', 'Rule'])
    else:
        logger.error(f'Unable to import iptc due to an error {err}')


@dataclass
class Rule:
    chain: str
    protocol: str
    port: Optional[int] = None
    icmp_type: Optional[str] = None
    action: str = 'accept'


class NFTablesError(Exception):
    pass


class NFTablesManager:
    def __init__(self, family: str = 'inet', table: str = 'filter', chain: str = 'input') -> None:
        self.nft = nftables.Nftables()
        self.nft.set_json_output(True)
        self.family = family
        self.table = table
        self.chain = chain

    def execute_cmd(self, json_cmd: dict) -> None:
        try:
            rc, output, error = self.nft.json_cmd(json_cmd)
            if rc != 0:
                raise NFTablesError(f'Command failed: {error}')
            return output
        except Exception as e:
            logger.error('Failed to execute command: %s', e)
            raise NFTablesError(e)

    def get_chains(self) -> list[str]:
        try:
            rc, output, error = self.nft.cmd(f'list chains {self.family}')
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

    def chain_exists(self, chain_name: str) -> bool:
        return chain_name in self.get_chains()

    def create_chain_if_not_exists(
        self, chain: str, hook: str, priority: int = 0, policy: str = 'accept'
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
                                'priority': priority,
                                'policy': policy,
                            }
                        }
                    }
                ]
            }
            self.execute_cmd(cmd)
            logger.info('Created new chain: %s', chain)
        else:
            logger.info('Chain already exists: %s', chain)

    def table_exists(self) -> bool:
        try:
            rc, output, error = self.nft.cmd(f'list table {self.family} {self.table}')
            return rc == 0
        except Exception:
            return False

    def create_table_if_not_exists(self) -> None:
        """Create table only if it doesn't exist"""
        if not self.table_exists():
            cmd = {'nftables': [{'add': {'table': {'family': self.family, 'name': self.table}}}]}
            self.execute_cmd(cmd)
            logger.info('Created new table: %s', self.table)
        else:
            logger.info('Table already exists: %s', self.table)

    def get_rules(self, chain: str) -> list[dict]:
        """Get existing rules for a chain"""
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
            if rule.get('expr') == new_rule_expr:
                return True
        return False

    def add_rule_if_not_exists(self, rule: Rule) -> None:
        expr = []

        if rule.protocol in ['tcp', 'udp']:
            if rule.port:
                expr.append(
                    {
                        'match': {
                            'left': {'payload': {'protocol': rule.protocol, 'field': 'dport'}},
                            'op': '==',
                            'right': rule.port,
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
                'Added new rule to chain %s: %s port %s', rule.chain, rule.protocol, rule.port
            )
        else:
            logger.info(
                'Rule already exists in chain %s: %s port %s', rule.chain, rule.protocol, rule.port
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
            {'accept': None},
        ]
        if not self.rule_exists(chain, expr):
            json_cmd = {
                'nftables': [
                    {
                        'add': {
                            'rule': {
                                'family': 'inet',
                                'table': 'filter',
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

    def setup_firewall(self) -> None:
        """Setup firewall rules"""
        try:
            self.create_table_if_not_exists()

            base_chains_config = {
                self.chain: {'hook': 'input', 'policy': 'accept'},
                'forward': {'hook': 'forward', 'policy': 'drop'},
                'output': {'hook': 'output', 'policy': 'accept'},
            }

            for chain, config in base_chains_config.items():
                self.create_chain_if_not_exists(
                    chain=chain, hook=config['hook'], policy=config['policy']
                )

            self.add_connection_tracking_rule(self.chain)

            tcp_ports = [get_ssh_port(), 8080, 443, 53, 3009, 9100]
            for port in tcp_ports:
                self.add_rule_if_not_exists(Rule(chain=chain, protocol='tcp', port=port))

            self.add_rule_if_not_exists(Rule(chain=chain, protocol='udp', port=53))
            self.add_loopback_rule(chain=chain)

            icmp_types = ['destination-unreachable', 'source-quench', 'time-exceeded']
            for icmp_type in icmp_types:
                self.add_rule_if_not_exists(Rule(chain=chain, protocol='icmp', icmp_type=icmp_type))

            self.add_rule_if_not_exists(Rule(chain=chain, protocol='tcp', action='drop'))
            self.add_rule_if_not_exists(Rule(chain=chain, protocol='udp', action='drop'))

        except Exception as e:
            logger.error('Failed to setup firewall: %s', e)
            raise


def configure_nftables() -> None:
    nft_mgr = NFTablesManager()
    nft_mgr.setup_firewall()
    logger.info('Firewall setup completed successfully')
