import inspect

from skale.utils.helper import private_key_to_address
from web3 import Web3

from core.config import URLS, LONG_LINE
from core.helper import get_node_creds, construct_url, get_request
from tools.helper import write_json
from configs.node import LOCAL_WALLET_FILEPATH


def set_wallet_by_pk(private_key):
    address = private_key_to_address(private_key)
    address_fx = Web3.toChecksumAddress(address)
    local_wallet = {'address': address_fx, 'private_key': private_key}
    write_json(LOCAL_WALLET_FILEPATH, local_wallet)
    print(f'Local wallet updated: {local_wallet["address"]}')


def get_wallet_info(config, format):
    host, cookies = get_node_creds(config)
    url = construct_url(host, URLS['wallet_info'])

    response = get_request(url, cookies)
    if response is None:
        return None

    json = response.json()
    data = json['data']

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
