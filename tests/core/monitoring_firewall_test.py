from pathlib import Path
from unittest.mock import patch

import pytest

import node_cli.core.nftables as firewall
from node_cli.core.nftables import NFTablesManager, Rule


@pytest.fixture
def monitoring_firewall(monkeypatch, tmp_path):
    """Run only in the isolated nftables test container (requires NET_ADMIN)."""
    monkeypatch.setenv('SSH_PORT', '22')
    monkeypatch.setenv('MONITORING_CONTAINERS', 'True')
    monkeypatch.delenv('SCHAIN_BASE_PORT', raising=False)
    monkeypatch.delenv('FIREWALL_DEFAULT_DROP', raising=False)
    monkeypatch.setattr(firewall, 'NODE_CONFIG_PATH', str(tmp_path / 'node.json'))
    monkeypatch.setattr(firewall, 'NFTABLES_USER_CONFIG_PATH', str(tmp_path / 'user.conf'))
    monkeypatch.setattr(firewall, 'NFTABLES_SKALE_BASE_CONFIG_PATH', str(tmp_path / 'base.conf'))
    monkeypatch.setattr(firewall, 'NFTABLES_CHAIN_CONFIG_WILDCARD', str(tmp_path / 'chains/*'))
    (tmp_path / 'chains').mkdir()
    (tmp_path / 'user.conf').touch()
    manager = NFTablesManager(table='monitoring_test')
    manager.create_table_if_not_exists()
    manager.create_chain_if_not_exists(manager.chain, hook='input')
    try:
        yield manager
    finally:
        manager.execute_cmd(
            {'nftables': [{'delete': {'table': {'family': manager.family, 'name': manager.table}}}]}
        )


@pytest.mark.parametrize('legacy_rule_copies', [0, 1, 2])
def test_monitoring_accepts_absent_after_setup_and_reload(monitoring_firewall, legacy_rule_copies):
    manager = monitoring_firewall
    expressions = [Rule(manager.chain, 'tcp', port).to_expr() for port in (8080, 9100)]
    for _ in range(legacy_rule_copies):
        for expr in expressions:
            manager._execute_rule_with_op('add', manager.chain, expr)

    for _ in range(2):
        manager.setup_firewall()
        assert manager.get_chain_policy(manager.chain) == 'drop'
        for expr in expressions:
            assert not manager.rule_exists(manager.chain, expr)
        manager.verify_critical_accepts()

    firewall.save_nftables_base_rules(manager.get_base_ruleset())
    manager.execute_cmd(
        {'nftables': [{'delete': {'table': {'family': manager.family, 'name': manager.table}}}]}
    )
    rc, _, error = manager.nft.cmd(f'include "{firewall.NFTABLES_SKALE_BASE_CONFIG_PATH}"')
    assert rc == 0, error
    assert manager.get_chain_policy(manager.chain) == 'drop'
    for expr in expressions:
        assert not manager.rule_exists(manager.chain, expr)
    manager.verify_critical_accepts()


def test_monitoring_cleanup_preserves_explicit_user_rules(monitoring_firewall):
    manager = monitoring_firewall
    Path(firewall.NFTABLES_USER_CONFIG_PATH).write_text('tcp dport 8080 counter accept\n')
    manager.add_rule(Rule(manager.chain, 'tcp', 8080))
    manager.setup_firewall()
    expr = Rule(manager.chain, 'tcp', 8080).to_expr()
    assert not manager.rule_exists(manager.chain, expr)
    assert manager.rule_exists(firewall.USER_CHAIN, expr)


def test_monitoring_cleanup_preserves_custom_ssh_port(monitoring_firewall, monkeypatch):
    monkeypatch.setenv('SSH_PORT', '9100')
    manager = monitoring_firewall
    manager.add_rule(Rule(manager.chain, 'tcp', 9100))
    with patch.object(
        manager, 'delete_rule_by_handle', wraps=manager.delete_rule_by_handle
    ) as delete:
        manager.setup_firewall()
        delete.assert_not_called()
    manager.verify_critical_accepts()
    assert manager.rule_exists(manager.chain, Rule(manager.chain, 'tcp', 9100).to_expr())
