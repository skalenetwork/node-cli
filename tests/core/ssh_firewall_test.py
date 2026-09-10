from unittest.mock import Mock, patch

import pytest

from node_cli.core.nftables import NFTablesError, NFTablesManager, Rule, conntrack_accept_expr


@pytest.fixture
def manager():
    # These checks exercise rule generation without accessing the host firewall.
    manager = NFTablesManager.__new__(NFTablesManager)
    manager.chain = 'skale'
    return manager


def test_allow_all_ssh_ports(manager):
    rules = []
    with (
        patch('node_cli.core.nftables.get_ssh_ports', return_value=[2200, 2222]),
        patch.object(manager, '_ensure_rule'),
        patch.object(manager, 'remove_misordered_udp_drop'),
        patch.object(manager, 'add_rule', side_effect=rules.append),
    ):
        manager._add_service_accepts(enable_monitoring=False)
    allowed_tcp_ports = {rule.first_port for rule in rules if rule.protocol == 'tcp'}
    assert {2200, 2222} <= allowed_tcp_ports
    assert 22 not in allowed_tcp_ports


def test_refuse_drop_until_all_ssh_ports_are_allowed(manager):
    installed = [conntrack_accept_expr(), Rule('skale', 'tcp', 2200).to_expr()]
    with (
        patch('node_cli.core.nftables.get_ssh_ports', return_value=[2200, 2222]),
        patch.object(manager, 'get_rules', side_effect=lambda _: [{'expr': e} for e in installed]),
        patch.object(manager, 'get_chain_policy', return_value='accept'),
        patch.object(manager, 'update_chain_policy') as update_policy,
    ):
        with pytest.raises(NFTablesError, match='ssh port 2222'):
            manager.ensure_default_drop()
        update_policy.assert_not_called()
        installed.append(Rule('skale', 'tcp', 2222).to_expr())
        manager.ensure_default_drop()
        update_policy.assert_called_once_with(chain='skale', policy='drop')


def test_detection_failure_prevents_drop(manager):
    manager.update_chain_policy = Mock()
    with patch(
        'node_cli.core.nftables.get_ssh_ports', side_effect=RuntimeError('SSH_PORT required')
    ):
        with pytest.raises(RuntimeError, match='SSH_PORT'):
            manager.ensure_default_drop()
    manager.update_chain_policy.assert_not_called()
