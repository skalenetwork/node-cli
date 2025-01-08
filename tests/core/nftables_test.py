import pytest
from unittest.mock import Mock, patch
import json
import nftables


from node_cli.core.nftables import NFTablesManager, Rule


@pytest.fixture(scope='module')
def nft_manager():
    """Returns a NFTablesManager instance"""
    manager = NFTablesManager(family='inet', table='filter')
    try:
        yield manager
    finally:
        manager.flush()


@pytest.fixture
def mock_nft_output():
    """Fixture for mock nftables output"""
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
    """Test initialization"""
    assert nft_manager.family == 'inet'
    assert nft_manager.table == 'filter'
    assert isinstance(nft_manager.nft, nftables.Nftables)


@patch('nftables.Nftables.json_cmd')
def test_execute_cmd_success(mock_json_cmd, nft_manager):
    """Test successful command execution"""
    mock_json_cmd.return_value = (0, '', '')
    cmd = {'nftables': [{'add': {'table': {'family': 'inet', 'name': 'filter'}}}]}

    nft_manager.execute_cmd(cmd)
    mock_json_cmd.assert_called_once_with(cmd)


@patch('nftables.Nftables.json_cmd')
def test_execute_cmd_failure(mock_json_cmd, nft_manager):
    """Test command execution failure"""
    mock_json_cmd.return_value = (1, '', 'Error message')
    cmd = {'nftables': [{'add': {'table': {'family': 'inet', 'name': 'filter'}}}]}

    with pytest.raises(Exception) as exc_info:
        nft_manager.execute_cmd(cmd)
    assert 'Command failed: Error message' in str(exc_info.value)


@patch('nftables.Nftables.cmd')
def test_get_chains(mock_cmd, nft_manager, mock_nft_output):
    """Test getting chains"""
    mock_cmd.return_value = (0, json.dumps(mock_nft_output), '')

    chains = nft_manager.get_chains()
    assert 'INPUT' in chains
    mock_cmd.assert_called_once_with('list chains inet')


@patch('nftables.Nftables.cmd')
def test_chain_exists(mock_cmd, nft_manager, mock_nft_output):
    """Test chain existence check"""
    mock_cmd.return_value = (0, json.dumps(mock_nft_output), '')

    assert nft_manager.chain_exists('INPUT')
    assert not nft_manager.chain_exists('nonexistent')


@patch.object(NFTablesManager, 'execute_cmd')
@patch.object(NFTablesManager, 'chain_exists')
def test_create_chain_if_not_exists(mock_exists, mock_execute, nft_manager):
    """Test chain creation"""
    mock_exists.return_value = False

    nft_manager.create_chain_if_not_exists('INPUT', 'input')
    mock_execute.assert_called_once()


@pytest.mark.parametrize(
    'rule_data',
    [
        {'chain': 'INPUT', 'protocol': 'tcp', 'port': 80, 'action': 'accept'},
        {'chain': 'INPUT', 'protocol': 'udp', 'port': 53, 'action': 'accept'},
        {'chain': 'INPUT', 'protocol': 'icmp', 'icmp_type': 'echo-request', 'action': 'accept'},
    ],
)
@patch.object(NFTablesManager, 'execute_cmd')
@patch.object(NFTablesManager, 'rule_exists')
def test_add_rule(mock_exists, mock_execute, nft_manager, rule_data):
    """Test rule addition with different types"""
    mock_exists.return_value = False

    rule = Rule(**rule_data)
    nft_manager.add_rule(rule)
    mock_execute.assert_called_once()


@patch.object(NFTablesManager, 'execute_cmd')
def test_setup_firewall(mock_execute, nft_manager):
    """Test complete firewall setup"""
    with patch.multiple(
        NFTablesManager,
        table_exists=Mock(return_value=False),
        chain_exists=Mock(return_value=False),
        rule_exists=Mock(return_value=False),
    ):
        nft_manager.setup_firewall()
        assert mock_execute.called


def test_invalid_protocol(nft_manager):
    """Test adding rule with invalid protocol"""
    rule = Rule(chain='INPUT', protocol='invalid', port=80)
    with pytest.raises(Exception):
        nft_manager.add_rule(rule)
