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
    claim_all_fees,
    set_fee_rate,
    claim_fees,
    send_fees,
    get_earned_fee_amount,
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


@staking.command('claim-all-fees', help='Claim all fees')
@click.option(
    '--yes',
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt='Are you sure you want to claim all fees?',
)
def _claim_all_fees() -> None:
    claim_all_fees()


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


@staking.command('claim-fees', help='Claim fees amount (FAIR)')
@click.argument('amount', type=float)
@click.option(
    '--yes',
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt='Are you sure you want to claim fees?',
)
def _claim_fees(amount: float) -> None:
    claim_fees(amount)


@staking.command('send-fees', help='Send fees to address (or all with --all)')
@click.argument('to')
@click.argument('value', type=float, required=False)
@click.option('--all', 'send_all', is_flag=True, help='Send all fees to address')
@click.option(
    '--yes',
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt='Are you sure you want to send fees?',
)
def _send_fees(to: str, value: float | None, send_all: bool) -> None:
    if value is None and not send_all:
        raise click.UsageError('Provide <VALUE> or use --all')
    send_fees(to, None if send_all else value)


@staking.command('get-earned-fee-amount', help='Get earned fee amount')
def _get_earned_fee_amount() -> None:
    get_earned_fee_amount()
