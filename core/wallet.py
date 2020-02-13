#   -*- coding: utf-8 -*-
#
#   This file is part of skale-node-cli
#
#   Copyright (C) 2019 SKALE Labs
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

import inspect

from skale.utils.web3_utils import private_key_to_address
from web3 import Web3

from configs import ROUTES, LONG_LINE, LOCAL_WALLET_FILEPATH
from core.helper import construct_url, get_request
from tools.helper import write_json


def set_wallet_by_pk(private_key):
    address = private_key_to_address(private_key)
    address_fx = Web3.toChecksumAddress(address)
    local_wallet = {'address': address_fx, 'private_key': private_key}
    write_json(LOCAL_WALLET_FILEPATH, local_wallet)
    print(f'Local wallet updated: {local_wallet["address"]}')


def get_wallet_info(config, format):
    url = construct_url(ROUTES['wallet_info'])

    response = get_request(url)
    if response is None:
        return None

    json_data = response.json()
    data = json_data['data']
    if format == 'json':
        print(data)
    else:
        print_wallet_info(data)


def print_wallet_info(wallet):
    print(inspect.cleandoc(f'''
        {LONG_LINE}
        Address: {wallet['address'].lower()}
        ETH balance: {wallet['eth_balance']} ETH
        SKALE balance: {wallet['skale_balance']} SKALE
        {LONG_LINE}
    '''))
