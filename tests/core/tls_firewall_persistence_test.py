import json
from uuid import uuid4

import pytest

from node_cli.core import nftables as firewall


@pytest.mark.parametrize('certificates', [False, True])
def test_tls_ports_survive_ruleset_restore(tmp_path, monkeypatch, certificates):
    pytest.importorskip('nftables')
    table = f'tls_test_{uuid4().hex}'
    manager = firewall.NFTablesManager(table=table)
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

    def command(text):
        rc, output, error = manager.nft.cmd(text)
        assert rc == 0, error
        return output

    def ports():
        data = json.loads(command(f'list set inet {table} skale_tls_ports'))
        return sorted(
            next(item['set'].get('elem', []) for item in data['nftables'] if 'set' in item)
        )

    command(f'add table inet {table}\nadd chain inet {table} skale')
    try:
        manager.sync_tls_accepts()
        manager.sync_tls_accepts()
        assert len(manager.get_rules('skale')) == 1
        firewall.save_nftables_base_rules(manager.get_base_ruleset())
        command(f'delete table inet {table}\n' + base_config.read_text())
        assert ports() == ([311, 443] if certificates else [])

        command(f'add element inet {table} skale_tls_ports {{ 311, 443 }}')
        command(f'add element inet {table} skale_tls_ports {{ 311, 443 }}')
        (chains / 'tls-ports.conf').write_text(
            'set skale_tls_ports { type inet_service; elements = { 311, 443 }; }\n'
        )
        command(f'delete table inet {table}\n' + base_config.read_text())
        assert ports() == [311, 443]

        certificates = False
        manager.sync_tls_accepts()
        assert ports() == []
    finally:
        command(f'delete table inet {table}')
