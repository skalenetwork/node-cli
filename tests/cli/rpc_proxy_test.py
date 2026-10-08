import mock
import pytest

from node_cli.cli.fair_node import node as fair_node
from node_cli.cli.node import node
from node_cli.cli.passive_fair_node import passive_node as passive_fair_node
from node_cli.cli.passive_node import passive_node
from node_cli.cli.rpc_proxy import rpc_proxy
from node_cli.core.node_options import NodeOptions
from tests.helper import run_command


def test_rpc_proxy_command(active_node_option, inited_node):
    with mock.patch('node_cli.utils.decorators.is_user_valid', return_value=True):
        result = run_command(rpc_proxy, ['on'])
        assert result.exit_code == 0, result.output
        assert NodeOptions().rpc_proxy is True

        result = run_command(rpc_proxy, ['default'])
        assert result.exit_code == 0, result.output
        assert NodeOptions().rpc_proxy is None

        result = run_command(rpc_proxy, ['sideways'])
        assert result.exit_code == 2


@pytest.mark.parametrize(
    'group',
    [node, passive_node, fair_node, passive_fair_node],
    ids=['node', 'passive_node', 'fair_node', 'passive_fair_node'],
)
def test_rpc_proxy_command_registered(group):
    assert group.commands['rpc-proxy'] is rpc_proxy
