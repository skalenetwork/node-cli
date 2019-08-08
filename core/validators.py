import requests
from core.config import URLS, LONG_LINE
from core.helper import get_node_creds, construct_url, get_request, print_err_response


def get_validators_info(config, format):
    host, cookies = get_node_creds(config)
    url = construct_url(host, URLS['validators_info'])

    response = get_request(url, cookies)
    if response is None:
        return None

    json = response.json()
    data = json['data']

    if format == 'json':
        print(data)
    else:
        pass
        #print_wallet_info(data)
