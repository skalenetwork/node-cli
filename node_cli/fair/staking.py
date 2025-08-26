#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
#
#   Copyright (C) 2025-Present SKALE Labs
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

from typing import Any, Optional

from node_cli.core.host import is_node_inited
from node_cli.utils.exit_codes import CLIExitCodes
from node_cli.utils.helper import error_exit, post_request

BLUEPRINT_NAME = 'fair-staking'


def _handle_response(status: str, payload: Any, success: Optional[str] = None) -> None:
    if status == 'ok':
        print(success if success is not None else 'OK')
    else:
        error_exit(payload, exit_code=CLIExitCodes.BAD_API_RESPONSE)


def add_allowed_receiver(receiver: str) -> None:
    if not is_node_inited():
        print('Node is not initialized')
        return
    status, payload = post_request(
        blueprint=BLUEPRINT_NAME, method='add-allowed-receiver', json={'receiver': receiver}
    )
    _handle_response(status, payload, success=f'Allowed receiver added: {receiver}')


def remove_allowed_receiver(receiver: str) -> None:
    if not is_node_inited():
        print('Node is not initialized')
        return
    status, payload = post_request(
        blueprint=BLUEPRINT_NAME, method='remove-allowed-receiver', json={'receiver': receiver}
    )
    _handle_response(status, payload, success=f'Allowed receiver removed: {receiver}')


def send_all_fees(to: str) -> None:
    if not is_node_inited():
        print('Node is not initialized')
        return
    status, payload = post_request(
        blueprint=BLUEPRINT_NAME, method='send-all-fees', json={'to': to}
    )
    _handle_response(status, payload, success=f'All fees sent to {to}')


def claim_all_fees() -> None:
    if not is_node_inited():
        print('Node is not initialized')
        return
    status, payload = post_request(blueprint=BLUEPRINT_NAME, method='claim-all-fees')
    _handle_response(status, payload, success='All fees claimed')


def set_fee_rate(fee_rate: int) -> None:
    if not is_node_inited():
        print('Node is not initialized')
        return
    status, payload = post_request(
        blueprint=BLUEPRINT_NAME, method='set-fee-rate', json={'feeRate': fee_rate}
    )
    _handle_response(status, payload, success=f'Fee rate set to {fee_rate}')


def claim_fees(amount: float) -> None:
    if not is_node_inited():
        print('Node is not initialized')
        return
    status, payload = post_request(
        blueprint=BLUEPRINT_NAME, method='claim-fees', json={'amount': amount}
    )
    _handle_response(status, payload, success=f'Fees claimed: {amount}')


def send_fees(to: str, amount: float) -> None:
    if not is_node_inited():
        print('Node is not initialized')
        return
    status, payload = post_request(
        blueprint=BLUEPRINT_NAME, method='send-fees', json={'to': to, 'amount': amount}
    )
    _handle_response(status, payload, success=f'Fees sent: {amount} to {to}')


def get_earned_fee_amount() -> None:
    if not is_node_inited():
        print('Node is not initialized')
        return
    status, payload = post_request(blueprint=BLUEPRINT_NAME, method='get-earned-fee-amount')
    if status == 'ok' and isinstance(payload, dict):
        amount_wei = payload.get('amount_wei')
        amount_ether = payload.get('amount_ether')
        print(f'Earned fee amount: {amount_wei} wei ({amount_ether} FAIR)')
        return
    error_exit(payload, exit_code=CLIExitCodes.BAD_API_RESPONSE)
