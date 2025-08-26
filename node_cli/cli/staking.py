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
    send_all_fees,
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


@staking.command('add-allowed-receiver', help='Add allowed receiver')
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


@staking.command('remove-allowed-receiver', help='Remove allowed receiver')
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


@staking.command('send-all-fees', help='Send all fees to address')
@click.argument('to')
@click.option(
    '--yes',
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt='Are you sure you want to send all fees?',
)
def _send_all_fees(to: str) -> None:
    send_all_fees(to)


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


@staking.command('send-fees', help='Send fees to address')
@click.argument('to')
@click.argument('amount', type=float)
@click.option(
    '--yes',
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt='Are you sure you want to send fees?',
)
def _send_fees(to: str, amount: float) -> None:
    send_fees(to, amount)


@staking.command('get-earned-fee-amount', help='Get earned fee amount')
def _get_earned_fee_amount() -> None:
    get_earned_fee_amount()
