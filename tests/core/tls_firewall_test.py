from unittest.mock import Mock, patch

import pytest

from node_cli.core.nftables import NFTablesError, NFTablesManager, Rule, sync_tls_ports

TLS_RULES = [Rule('skale', 'tcp', 443), Rule('skale', 'tcp', 311)]


@pytest.fixture
def manager(tmp_path, monkeypatch):
    # These checks exercise rule generation without accessing the host firewall.
    manager = NFTablesManager.__new__(NFTablesManager)
    manager.chain = 'skale'
    manager.family = 'inet'
    manager.table = 'firewall'
    manager.nft = Mock()
    manager.nft.cmd.return_value = (0, '', '')
    monkeypatch.setattr('node_cli.core.nftables.NFTABLES_CHAIN_FOLDER_PATH', tmp_path)
    return manager


def service_accepts(manager, certs, ssh_ports, installed=()):
    """Rules added and handles deleted by one pass over a chain holding the installed rules"""
    added, deleted = [], []
    rules = [{'handle': handle, 'expr': rule.to_expr()} for handle, rule in enumerate(installed)]
    with (
        patch('node_cli.core.nftables.check_ssl_certs', return_value=certs),
        patch('node_cli.core.nftables.get_ssh_ports', return_value=ssh_ports),
        patch.object(manager, '_ensure_rule'),
        patch.object(manager, 'remove_misordered_udp_drop'),
        patch.object(manager, 'get_rules', return_value=rules),
        patch.object(manager, 'add_rule', side_effect=added.append),
        patch.object(manager, 'delete_rule_by_handle', side_effect=deleted.append),
    ):
        manager._add_service_accepts()
    return added, deleted


def test_tls_ports_open_with_certificates(manager, tmp_path):
    added, deleted = service_accepts(manager, certs=True, ssh_ports=[22])
    assert not any(rule in added for rule in TLS_RULES)
    assert deleted == []
    assert 'elements = { 443, 311 }' in (tmp_path / 'tls-ports.conf').read_text()
    assert (
        'add element inet firewall skale_tls_ports { 443, 311 }'
        in (manager.nft.cmd.call_args.args[0])
    )


def test_tls_ports_closed_without_certificates(manager, tmp_path):
    # a setup that opened the ports unconditionally left accepts behind, some of them twice
    installed = [Rule('skale', 'tcp', 22), *TLS_RULES, Rule('skale', 'tcp', 80), TLS_RULES[0]]
    added, deleted = service_accepts(manager, certs=False, ssh_ports=[22], installed=installed)
    assert not any(rule in added for rule in TLS_RULES)
    assert deleted == [1, 2, 4]
    # the plain HTTP services do not depend on certificates
    assert Rule('skale', 'tcp', 80) in added
    assert Rule('skale', 'tcp', 3009) in added
    assert (tmp_path / 'tls-ports.conf').read_text() == (
        'set skale_tls_ports { type inet_service; }\n'
    )
    assert 'add element' not in manager.nft.cmd.call_args.args[0]


def test_closing_tls_ports_keeps_ssh_reachable(manager):
    added, deleted = service_accepts(manager, certs=False, ssh_ports=[443], installed=TLS_RULES)
    assert Rule('skale', 'tcp', 443) in added
    assert deleted == [1]


def test_sync_tls_ports_saves_the_rules_for_the_next_boot():
    with (
        patch('node_cli.core.nftables.NFTablesManager') as manager_cls,
        patch('node_cli.core.nftables.save_nftables_base_rules') as save,
    ):
        manager_cls.return_value.get_base_ruleset.return_value = 'table inet firewall {}'
        sync_tls_ports()
    manager_cls.return_value.sync_tls_accepts.assert_called_once_with()
    save.assert_called_once_with('table inet firewall {}')


def test_tls_set_failure_preserves_saved_ports(manager, tmp_path):
    path = tmp_path / 'tls-ports.conf'
    path.write_text('previous')
    manager.nft.cmd.return_value = (1, '', 'permission denied')
    with patch('node_cli.core.nftables.check_ssl_certs', return_value=True):
        with pytest.raises(NFTablesError, match='permission denied'):
            manager.sync_tls_accepts()
    assert path.read_text() == 'previous'


def test_tls_set_accept_precedes_removal_of_legacy_rules(manager):
    events = []
    with (
        patch('node_cli.core.nftables.check_ssl_certs', return_value=True),
        patch.object(manager, '_ensure_rule', side_effect=lambda *a, **kw: events.append(a)),
        patch.object(manager, '_remove_tcp_accepts', side_effect=lambda *a: events.append(a)),
    ):
        manager.sync_tls_accepts()
    chain, expr = events[0]
    assert chain == 'skale'
    assert expr[0]['match']['right'] == '@skale_tls_ports'
    assert expr[-1] == {'accept': None}
    assert events[1] == ((443, 311),)
