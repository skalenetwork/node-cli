from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from node_cli.core import nftables as firewall


@pytest.mark.parametrize('certificates', [False, True])
def test_tls_ports_are_saved_for_restore(tmp_path, monkeypatch, certificates):
    nft = Mock()
    nft.cmd.return_value = (0, '', '')
    nft.json_cmd.return_value = (0, '', '')
    monkeypatch.setattr(firewall, 'nftables', SimpleNamespace(Nftables=lambda: nft), raising=False)
    manager = firewall.NFTablesManager()
    monkeypatch.setattr(firewall, 'NFTablesManager', lambda: manager)
    monkeypatch.setattr(manager, 'get_rules', lambda chain: [])
    monkeypatch.setattr(
        manager,
        'get_base_ruleset',
        lambda: (
            'table inet firewall {\n'
            '\tchain skale {\n'
            '\t\ttcp dport @skale_tls_ports counter accept\n'
            '\t}\n'
            '}\n'
        ),
    )
    chains = tmp_path / 'chains'
    chains.mkdir()
    user_config = tmp_path / 'user.conf'
    user_config.touch()
    base_config = tmp_path / 'base.conf'
    monkeypatch.setattr(firewall, 'NFTABLES_CHAIN_FOLDER_PATH', chains)
    monkeypatch.setattr(firewall, 'NFTABLES_CHAIN_CONFIG_WILDCARD', str(chains / '*.conf'))
    monkeypatch.setattr(firewall, 'NFTABLES_USER_CONFIG_PATH', str(user_config))
    monkeypatch.setattr(firewall, 'NFTABLES_SKALE_BASE_CONFIG_PATH', str(base_config))
    monkeypatch.setattr(firewall, 'check_ssl_certs', lambda: certificates)
    monkeypatch.setattr(firewall, 'get_ssh_ports', lambda: [22])

    for certificates in (certificates, True, True, False):
        firewall.sync_tls_ports()
        elements = ' elements = { 443, 311 };' if certificates else ''
        assert (chains / 'tls-ports.conf').read_text() == (
            f'set skale_tls_ports {{ type inet_service;{elements} }}\n'
        )
        commands = nft.cmd.call_args.args[0]
        assert 'flush set inet firewall skale_tls_ports\n' in commands
        if certificates:
            assert 'add element inet firewall skale_tls_ports { 443, 311 }\n' in commands
        else:
            assert 'add element' not in commands

        saved = base_config.read_text()
        include = f'include "{chains}/*.conf"'
        assert saved.count(include) == 1
        assert saved.index(include) < saved.index('tcp dport @skale_tls_ports')
        assert f'include "{user_config}"' in saved
        assert sorted(path.name for path in chains.glob('*.conf')) == ['tls-ports.conf']
