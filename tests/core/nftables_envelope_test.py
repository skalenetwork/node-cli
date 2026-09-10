from unittest.mock import patch

import pytest

from node_cli.core.nftables import NFTablesManager, Rule


@pytest.mark.parametrize(
    'old_range,new_range',
    [
        ((20128, 20191), (30000, 30063)),
        ((10000, 18191), (30000, 38191)),
        ((10000, 18191), (10000, 10063)),
        ((10000, 10063), (10000, 18191)),
    ],
)
def test_replace_envelope_preserves_current_range_and_unrelated_rules(old_range, new_range):
    manager = NFTablesManager.__new__(NFTablesManager)
    manager.chain = 'skale'
    current = Rule('skale', 'tcp', *new_range)
    rules = [
        {'handle': 1, 'expr': Rule('skale', 'tcp', *old_range).to_expr()},
        {'handle': 2, 'expr': current.to_expr()},
        {'handle': 3, 'expr': Rule('skale', 'tcp', 1026, 1031, action='drop').to_expr()},
        {'handle': 4, 'expr': Rule('skale', 'tcp', 5000, 5010).to_expr()},
        {'handle': 5, 'expr': Rule('skale', 'tcp', *old_range, action='drop').to_expr()},
    ]
    with (
        patch.object(manager, 'get_rules', return_value=rules),
        patch.object(manager, 'delete_rule_by_handle') as delete,
        patch.object(manager, 'add_rule') as add,
    ):
        manager._ensure_envelope(new_range)
        delete.assert_called_once_with(1)
        add.assert_called_once_with(current)
