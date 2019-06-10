import inspect
from cli.config import URLS, LONG_LINE
from cli.helper import get_node_creds, construct_url, get_request


def get_wallet_info(config, format):
    host, cookies = get_node_creds(config)
    url = construct_url(host, URLS['wallet_info'])

    response = get_request(url, cookies)
    if not response:
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
        ETH balance: {wallet['eth_balance']} wei
        SKALE balance: {wallet['skale_balance']} wei
        {LONG_LINE}
    '''))