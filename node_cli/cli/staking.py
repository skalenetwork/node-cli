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

import click

from node_cli.fair.staking import (
    add_allowed_receiver,
    remove_allowed_receiver,
    set_fee_rate,
    request_fees,
    request_send_fees,
    claim_request,
    get_earned_fee_amount,
    get_exit_requests,
)
from node_cli.utils.helper import abort_if_false


@click.group()
def staking_cli():
    pass


@staking_cli.group(help='Staking commands')
def staking():
    pass


@staking.command('add-receiver', help='Add allowed receiver')
@click.argument('receiver')
@click.option(
    '--yes',
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt='Are you sure you want to add allowed receiver?',
)
def _add_allowed_receiver(receiver: str) -> None:
    add_allowed_receiver(receiver)


@staking.command('remove-receiver', help='Remove allowed receiver')
@click.argument('receiver')
@click.option(
    '--yes',
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt='Are you sure you want to remove allowed receiver?',
)
def _remove_allowed_receiver(receiver: str) -> None:
    remove_allowed_receiver(receiver)


@staking.command('set-fee-rate', help='Set fee rate (uint16, basis points; 25 = 2.5%)')
@click.argument('fee_rate', type=int)
@click.option(
    '--yes',
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt='Are you sure you want to set fee rate?',
)
def _set_fee_rate(fee_rate: int) -> None:
    set_fee_rate(fee_rate)


@staking.command('request-fees', help='Create a request to claim fees (FAIR) or all with --all')
@click.argument('amount', type=float, required=False)
@click.option('--all', 'request_all', is_flag=True, help='Request all fees')
@click.option(
    '--yes',
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt='Are you sure you want to request fees?',
)
def _request_fees(amount: float | None, request_all: bool) -> None:
    if amount is None and not request_all:
        raise click.UsageError('Provide <AMOUNT> or use --all')
    request_fees(None if request_all else amount)


@staking.command(
    'request-send-fees',
    help='Create a request to send fees to address (or all with --all)',
)
@click.argument('to')
@click.argument('amount', type=float, required=False)
@click.option('--all', 'send_all', is_flag=True, help='Request to send all fees to address')
@click.option(
    '--yes',
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt='Are you sure you want to request to send fees?',
)
def _request_send_fees(to: str, amount: float | None, send_all: bool) -> None:
    if amount is None and not send_all:
        raise click.UsageError('Provide <AMOUNT> or use --all')
    request_send_fees(to, None if send_all else amount)


@staking.command('claim-request', help='Claim previously created request by request ID')
@click.argument('request_id', type=int)
@click.option(
    '--yes',
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt='Are you sure you want to claim this request?',
)
def _claim_request(request_id: int) -> None:
    claim_request(request_id)


@staking.command('earned-fee-amount', help='Get earned fee amount')
def _get_earned_fee_amount() -> None:
    get_earned_fee_amount()


@staking.command('exit-requests', help='Get exit requests for current wallet')
@click.option('--json', 'raw', is_flag=True, help='Output in JSON format')
def _get_exit_requests(raw: bool) -> None:
    get_exit_requests(raw=raw)
