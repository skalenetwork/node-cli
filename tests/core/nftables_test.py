import pytest
from unittest.mock import Mock, patch
import json
import nftables


import node_cli.core.nftables as nftables_core
from node_cli.core.nftables import (
    NFTablesError,
    NFTablesManager,
    Rule,
    get_schain_ports_envelope,
)


@pytest.fixture(scope='module')
def nft_manager():
    """Returns a NFTablesManager instance."""
    manager = NFTablesManager(family='inet', table='filter')
    try:
        yield manager
    finally:
        manager.flush()


@pytest.fixture
def mock_nft_output():
    """Fixture for mocking nftables output."""
    return {
        'nftables': [
            {'chain': {'family': 'inet', 'table': 'filter', 'name': 'INPUT', 'handle': 1}},
            {
                'rule': {
                    'family': 'inet',
                    'table': 'filter',
                    'chain': 'INPUT',
                    'handle': 2,
                    'expr': [
                        {
                            'match': {
                                'left': {'payload': {'protocol': 'tcp', 'field': 'dport'}},
                                'op': '==',
                                'right': 80,
                            }
                        },
                        {'accept': None},
                    ],
                }
            },
        ]
    }


def test_init(nft_manager):
    """Test initialization."""
    assert nft_manager.family == 'inet'
    assert nft_manager.table == 'filter'
    assert isinstance(nft_manager.nft, nftables.Nftables)


@patch('nftables.Nftables.json_cmd')
def test_execute_cmd_success(mock_json_cmd, nft_manager):
    """Test successful command execution."""
    mock_json_cmd.return_value = (0, '', '')
    cmd = {'nftables': [{'add': {'table': {'family': 'inet', 'name': 'filter'}}}]}

    nft_manager.execute_cmd(cmd)
    mock_json_cmd.assert_called_once_with(cmd)


@patch('nftables.Nftables.json_cmd')
def test_execute_cmd_failure(mock_json_cmd, nft_manager):
    """Test command execution failure."""
    mock_json_cmd.return_value = (1, '', 'Error message')
    cmd = {'nftables': [{'add': {'table': {'family': 'inet', 'name': 'filter'}}}]}

    with pytest.raises(Exception) as exc_info:
        nft_manager.execute_cmd(cmd)
    assert 'Command failed: Error message' in str(exc_info.value)


@patch('nftables.Nftables.cmd')
def test_get_chains(mock_cmd, nft_manager, mock_nft_output):
    """Test getting chains."""
    mock_cmd.return_value = (0, json.dumps(mock_nft_output), '')

    chains = nft_manager.get_chains()
    assert 'INPUT' in chains
    mock_cmd.assert_called_once_with('list chains inet')


@patch('nftables.Nftables.cmd')
def test_chain_exists(mock_cmd, nft_manager, mock_nft_output):
    """Test chain existence check."""
    mock_cmd.return_value = (0, json.dumps(mock_nft_output), '')

    assert nft_manager.chain_exists('INPUT')
    assert not nft_manager.chain_exists('nonexistent')


@patch.object(NFTablesManager, 'execute_cmd')
@patch.object(NFTablesManager, 'chain_exists')
def test_create_chain_if_not_exists(mock_exists, mock_execute, nft_manager):
    """Test chain creation."""
    mock_exists.return_value = False

    nft_manager.create_chain_if_not_exists('INPUT', 'input')
    mock_execute.assert_called_once()


@patch('nftables.Nftables.cmd')
def test_update_chain_policy_uses_given_policy(mock_cmd, nft_manager):
    """Test that policy update applies the requested policy."""
    mock_cmd.return_value = (0, '', '')
    with patch.object(NFTablesManager, 'chain_exists', return_value=True):
        nft_manager.update_chain_policy(chain='skale', policy='drop')
    assert mock_cmd.call_args[0][0] == 'add chain inet filter skale { policy drop ; }'

    mock_cmd.return_value = (1, '', 'some error')
    with patch.object(NFTablesManager, 'chain_exists', return_value=True):
        with pytest.raises(NFTablesError):
            nft_manager.update_chain_policy(chain='skale', policy='drop')


@patch('nftables.Nftables.cmd')
def test_get_chain_policy(mock_cmd, nft_manager):
    listing = {
        'nftables': [
            {
                'chain': {
                    'family': 'inet',
                    'table': 'filter',
                    'name': 'skale',
                    'hook': 'input',
                    'policy': 'drop',
                }
            }
        ]
    }
    mock_cmd.return_value = (0, json.dumps(listing), '')
    assert nft_manager.get_chain_policy('skale') == 'drop'

    mock_cmd.return_value = (1, '', 'No such file or directory')
    assert nft_manager.get_chain_policy('skale') is None


@pytest.mark.parametrize(
    'rule_data',
    [
        {'chain': 'INPUT', 'protocol': 'tcp', 'first_port': 80, 'action': 'accept'},
        {'chain': 'INPUT', 'protocol': 'udp', 'first_port': 53, 'action': 'accept'},
        {'chain': 'INPUT', 'protocol': 'icmp', 'icmp_type': 'echo-request', 'action': 'accept'},
    ],
)
@patch.object(NFTablesManager, 'execute_cmd')
@patch.object(NFTablesManager, 'rule_exists')
def test_add_rule(mock_exists, mock_execute, nft_manager, rule_data):
    """Test rule addition with different types."""
    mock_exists.return_value = False

    rule = Rule(**rule_data)
    nft_manager.add_rule(rule)
    mock_execute.assert_called_once()


@patch.object(NFTablesManager, 'execute_cmd')
@patch.object(NFTablesManager, 'rule_exists')
def test_add_rule_udp_uses_udp_payload(mock_exists, mock_execute, nft_manager):
    """Test that udp rules match udp dport, not tcp."""
    mock_exists.return_value = False

    nft_manager.add_rule(Rule(chain='INPUT', protocol='udp', first_port=53))
    expr = mock_execute.call_args[0][0]['nftables'][0]['add']['rule']['expr']
    assert expr[0]['match']['left']['payload'] == {'protocol': 'udp', 'field': 'dport'}


@patch.object(NFTablesManager, 'execute_cmd')
@patch.object(NFTablesManager, 'rule_exists')
def test_add_rule_icmpv6(mock_exists, mock_execute, nft_manager):
    """Test icmpv6 rule addition."""
    mock_exists.return_value = False

    nft_manager.add_rule(Rule(chain='INPUT', protocol='icmpv6', icmp_type='nd-neighbor-solicit'))
    expr = mock_execute.call_args[0][0]['nftables'][0]['add']['rule']['expr']
    assert expr[0]['match']['left']['payload'] == {'protocol': 'icmpv6', 'field': 'type'}
    assert expr[0]['match']['right'] == 'nd-neighbor-solicit'


@patch('nftables.Nftables.cmd')
def test_get_dynamic_chain_port_ranges(mock_cmd, nft_manager):
    """Test collection of port ranges covered by skale-admin chains."""
    listing = {
        'nftables': [
            {'chain': {'family': 'inet', 'table': 'filter', 'name': 'skale'}},
            {'chain': {'family': 'inet', 'table': 'filter', 'name': 'skale-test'}},
            {
                'rule': {
                    'family': 'inet',
                    'table': 'filter',
                    'chain': 'skale',
                    'expr': [
                        {
                            'match': {
                                'op': '==',
                                'left': {'payload': {'protocol': 'tcp', 'field': 'dport'}},
                                'right': 22,
                            }
                        },
                        {'accept': None},
                    ],
                }
            },
            {
                'rule': {
                    'family': 'inet',
                    'table': 'filter',
                    'chain': 'skale-test',
                    'expr': [
                        {
                            'match': {
                                'op': '==',
                                'left': {'payload': {'protocol': 'ip', 'field': 'saddr'}},
                                'right': '1.2.3.4',
                            }
                        },
                        {
                            'match': {
                                'op': '==',
                                'left': {'payload': {'protocol': 'tcp', 'field': 'dport'}},
                                'right': 10001,
                            }
                        },
                        {'accept': None},
                    ],
                }
            },
            {
                'rule': {
                    'family': 'inet',
                    'table': 'filter',
                    'chain': 'skale-test',
                    'expr': [
                        {
                            'match': {
                                'op': '==',
                                'left': {'payload': {'protocol': 'tcp', 'field': 'dport'}},
                                'right': {'range': [10000, 10063]},
                            }
                        },
                        {'drop': None},
                    ],
                }
            },
        ]
    }
    mock_cmd.return_value = (0, json.dumps(listing), '')
    assert nft_manager.get_dynamic_chain_port_ranges() == [('skale-test', 10000, 10063)]

    mock_cmd.return_value = (1, '', 'No such file or directory')
    assert nft_manager.get_dynamic_chain_port_ranges() == []


def test_validate_dynamic_ranges(nft_manager):
    """Test envelope validation against dynamic chain ranges."""
    with patch.object(
        NFTablesManager,
        'get_dynamic_chain_port_ranges',
        return_value=[('skale-test', 10064, 10127)],
    ):
        nft_manager.validate_dynamic_ranges((10000, 18191))
        with pytest.raises(NFTablesError):
            nft_manager.validate_dynamic_ranges((10128, 18191))


def test_verify_critical_accepts(nft_manager):
    with patch.object(NFTablesManager, 'rule_exists', return_value=True):
        nft_manager.verify_critical_accepts()
    with patch.object(NFTablesManager, 'rule_exists', return_value=False):
        with pytest.raises(NFTablesError):
            nft_manager.verify_critical_accepts()


def test_ensure_default_drop(nft_manager):
    with patch.multiple(
        NFTablesManager,
        validate_dynamic_ranges=Mock(),
        verify_critical_accepts=Mock(),
        get_chain_policy=Mock(return_value='accept'),
        update_chain_policy=Mock(),
    ):
        nft_manager.ensure_default_drop((10000, 18191))
        NFTablesManager.validate_dynamic_ranges.assert_called_once_with((10000, 18191))
        NFTablesManager.verify_critical_accepts.assert_called_once()
        NFTablesManager.update_chain_policy.assert_called_once_with(chain='skale', policy='drop')

    with patch.multiple(
        NFTablesManager,
        validate_dynamic_ranges=Mock(),
        verify_critical_accepts=Mock(),
        get_chain_policy=Mock(return_value='drop'),
        update_chain_policy=Mock(),
    ):
        nft_manager.ensure_default_drop((10000, 18191))
        NFTablesManager.update_chain_policy.assert_not_called()


def test_ensure_default_accept(nft_manager):
    with patch.multiple(
        NFTablesManager,
        get_chain_policy=Mock(return_value='drop'),
        update_chain_policy=Mock(),
    ):
        nft_manager.ensure_default_accept()
        NFTablesManager.update_chain_policy.assert_called_once_with(chain='skale', policy='accept')

    with patch.multiple(
        NFTablesManager,
        get_chain_policy=Mock(return_value='accept'),
        update_chain_policy=Mock(),
    ):
        nft_manager.ensure_default_accept()
        NFTablesManager.update_chain_policy.assert_not_called()


def test_remove_stale_envelope_rules(nft_manager):
    stale_rule = {
        'handle': 7,
        'expr': [
            {
                'match': {
                    'op': '==',
                    'left': {'payload': {'protocol': 'tcp', 'field': 'dport'}},
                    'right': {'range': [10000, 18191]},
                }
            },
            {'counter': None},
            {'accept': None},
        ],
    }
    current_rule = {
        'handle': 8,
        'expr': [
            {
                'match': {
                    'op': '==',
                    'left': {'payload': {'protocol': 'tcp', 'field': 'dport'}},
                    'right': {'range': [30000, 38191]},
                }
            },
            {'counter': None},
            {'accept': None},
        ],
    }
    sgx_drop_rule = {
        'handle': 9,
        'expr': [
            {
                'match': {
                    'op': '==',
                    'left': {'payload': {'protocol': 'tcp', 'field': 'dport'}},
                    'right': {'range': [1026, 1031]},
                }
            },
            {'counter': None},
            {'drop': None},
        ],
    }
    with patch.multiple(
        NFTablesManager,
        get_rules=Mock(return_value=[stale_rule, current_rule, sgx_drop_rule]),
        delete_rule_by_handle=Mock(),
    ):
        nft_manager.remove_stale_envelope_rules((30000, 38191))
        NFTablesManager.delete_rule_by_handle.assert_called_once_with(7)


def test_get_schain_ports_envelope_default(monkeypatch, tmp_path):
    monkeypatch.setattr(nftables_core, 'NODE_CONFIG_PATH', str(tmp_path / 'nonexistent.json'))
    assert get_schain_ports_envelope() == (10000, 18191)


def test_get_schain_ports_envelope_env_override(monkeypatch):
    monkeypatch.setenv('SCHAIN_BASE_PORT', '30000')
    assert get_schain_ports_envelope() == (30000, 38191)

    monkeypatch.setenv('SCHAIN_BASE_PORT', 'not-a-port')
    with pytest.raises(NFTablesError):
        get_schain_ports_envelope()

    monkeypatch.setenv('SCHAIN_BASE_PORT', '65000')
    with pytest.raises(NFTablesError):
        get_schain_ports_envelope()

    monkeypatch.setenv('SCHAIN_BASE_PORT', '1000')
    with pytest.raises(NFTablesError):
        get_schain_ports_envelope()


def test_get_schain_ports_envelope_from_node_config(monkeypatch, tmp_path):
    config_path = tmp_path / 'node_config.json'
    monkeypatch.setattr(nftables_core, 'NODE_CONFIG_PATH', str(config_path))

    # active node: node_base_port saved at registration wins
    config_path.write_text(
        json.dumps({'node_id': 1, 'node_base_port': 20128, 'schain_base_port': 30000})
    )
    assert get_schain_ports_envelope() == (20128, 28319)

    # passive/fair node: only schain_base_port is present
    config_path.write_text(json.dumps({'node_id': 1, 'schain_base_port': 20128}))
    assert get_schain_ports_envelope() == (20128, 28319)


@patch.object(NFTablesManager, 'execute_cmd')
def test_setup_firewall(mock_execute, nft_manager, monkeypatch, tmp_path):
    """Test complete firewall setup."""
    monkeypatch.setattr(nftables_core, 'NODE_CONFIG_PATH', str(tmp_path / 'nonexistent.json'))
    with patch.multiple(
        NFTablesManager,
        table_exists=Mock(return_value=False),
        chain_exists=Mock(return_value=False),
        rule_exists=Mock(return_value=False),
        verify_critical_accepts=Mock(),
        get_dynamic_chain_port_ranges=Mock(return_value=[]),
        get_chain_policy=Mock(return_value='accept'),
        update_chain_policy=Mock(),
    ):
        nft_manager.setup_firewall()
        assert mock_execute.called

        added_exprs = [
            call.args[0]['nftables'][0]['add']['rule']['expr']
            for call in mock_execute.call_args_list
            if 'rule' in call.args[0]['nftables'][0].get('add', {})
        ]
        envelope_exprs = [
            expr
            for expr in added_exprs
            if expr[0].get('match', {}).get('right') == {'range': [10000, 18191]}
            and {'accept': None} in expr
        ]
        assert len(envelope_exprs) == 1
        icmpv6_exprs = [
            expr
            for expr in added_exprs
            if expr[0].get('match', {}).get('left', {}).get('payload', {}).get('protocol')
            == 'icmpv6'
        ]
        assert len(icmpv6_exprs) == len(nftables_core.ICMPV6_ACCEPT_TYPES)

        NFTablesManager.update_chain_policy.assert_any_call(
            chain='INPUT', policy='accept', family='ip', table='filter'
        )
        NFTablesManager.update_chain_policy.assert_any_call(chain='skale', policy='drop')


@patch.object(NFTablesManager, 'execute_cmd')
def test_setup_firewall_default_drop_disabled(mock_execute, nft_manager, monkeypatch, tmp_path):
    """Test that FIREWALL_DEFAULT_DROP=False keeps the accept policy."""
    monkeypatch.setenv('FIREWALL_DEFAULT_DROP', 'False')
    monkeypatch.setattr(nftables_core, 'NODE_CONFIG_PATH', str(tmp_path / 'nonexistent.json'))
    with patch.multiple(
        NFTablesManager,
        table_exists=Mock(return_value=True),
        chain_exists=Mock(return_value=True),
        rule_exists=Mock(return_value=True),
        get_dynamic_chain_port_ranges=Mock(return_value=[]),
        ensure_default_drop=Mock(),
        ensure_default_accept=Mock(),
        update_chain_policy=Mock(),
    ):
        nft_manager.setup_firewall()
        NFTablesManager.ensure_default_drop.assert_not_called()
        NFTablesManager.ensure_default_accept.assert_called_once()


def test_invalid_protocol(nft_manager):
    """Test adding rule with invalid protocol."""
    rule = Rule(chain='INPUT', protocol='invalid', first_port=80)
    with pytest.raises(Exception):
        nft_manager.add_rule(rule)
