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

from typing import Any
import json
from datetime import datetime, timezone

from node_cli.utils.decorators import check_inited
from node_cli.utils.exit_codes import CLIExitCodes
from node_cli.utils.helper import error_exit, post_request

BLUEPRINT_NAME = 'fair-staking'


def _handle_response(status: str, payload: Any, success: str | None = None) -> None:
    if status == 'ok':
        print(success if success is not None else 'OK')
    else:
        error_exit(payload, exit_code=CLIExitCodes.BAD_API_RESPONSE)


@check_inited
def add_allowed_receiver(receiver: str) -> None:
    status, payload = post_request(
        blueprint=BLUEPRINT_NAME, method='add-receiver', json={'receiver': receiver}
    )
    _handle_response(status, payload, success=f'Allowed receiver added: {receiver}')


@check_inited
def remove_allowed_receiver(receiver: str) -> None:
    status, payload = post_request(
        blueprint=BLUEPRINT_NAME, method='remove-receiver', json={'receiver': receiver}
    )
    _handle_response(status, payload, success=f'Allowed receiver removed: {receiver}')


@check_inited
def request_fees(amount: float | None) -> None:
    json_data: dict[str, Any] = {}
    if amount is not None:
        json_data['amount'] = amount
    status, payload = post_request(blueprint=BLUEPRINT_NAME, method='request-fees', json=json_data)
    _handle_response(
        status,
        payload,
        success='All fees requested' if amount is None else f'Fees requested: {amount}',
    )


@check_inited
def request_send_fees(to: str, amount: float | None) -> None:
    json_data: dict[str, Any] = {'to': to}
    if amount is not None:
        json_data['amount'] = amount
    status, payload = post_request(
        blueprint=BLUEPRINT_NAME, method='request-send-fees', json=json_data
    )
    _handle_response(status, payload, success=f'Fees request to send to {to} created')


@check_inited
def set_fee_rate(fee_rate: int) -> None:
    status, payload = post_request(
        blueprint=BLUEPRINT_NAME, method='set-fee-rate', json={'feeRate': fee_rate}
    )
    _handle_response(status, payload, success=f'Fee rate set to {fee_rate}')


@check_inited
def claim_request(request_id: int) -> None:
    status, payload = post_request(
        blueprint=BLUEPRINT_NAME, method='claim-request', json={'requestId': request_id}
    )
    _handle_response(status, payload, success=f'Request claimed: {request_id}')


@check_inited
def get_earned_fee_amount() -> None:
    status, payload = post_request(blueprint=BLUEPRINT_NAME, method='get-earned-fee-amount')
    if status == 'ok' and isinstance(payload, dict):
        amount_wei = payload.get('amount_wei')
        amount_ether = payload.get('amount_ether')
        print(f'Earned fee amount: {amount_wei} wei ({amount_ether} FAIR)')
        return
    error_exit(payload, exit_code=CLIExitCodes.BAD_API_RESPONSE)


@check_inited
def get_exit_requests(raw: bool = False) -> None:
    status, payload = post_request(blueprint=BLUEPRINT_NAME, method='get-exit-requests')
    if status == 'ok' and isinstance(payload, dict):
        exit_requests = payload.get('exit_requests')
        if not isinstance(exit_requests, list):
            error_exit(payload, exit_code=CLIExitCodes.BAD_API_RESPONSE)
        if raw:
            print(json.dumps(exit_requests, indent=2))
            return
        for req in exit_requests:
            try:
                request_id = req.get('request_id')
                user = req.get('user')
                node_id = req.get('node_id')
                amount = req.get('amount')
                unlock_date = req.get('unlock_date')
                amount_fair = None
                if isinstance(amount, int):
                    amount_fair = amount / 10**18
                unlock_iso = None
                if isinstance(unlock_date, int):
                    unlock_iso = datetime.fromtimestamp(unlock_date, tz=timezone.utc).isoformat()
                base = (
                    f'request_id: {request_id} | user: {user} | node_id: {node_id} | '
                    f'amount_wei: {amount} | amount_fair: {amount_fair} | '
                    f'unlock_date: {unlock_date}'
                )
                print(base + (f' ({unlock_iso})' if unlock_iso else ''))
            except Exception:  # noqa: BLE001
                print(req)
        return
    error_exit(payload, exit_code=CLIExitCodes.BAD_API_RESPONSE)
