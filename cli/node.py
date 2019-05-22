import inspect
import requests
from cli.config import URLS, LONG_LINE
from cli.helper import get_node_creds, construct_url


def create_node(config, name, p2p_ip, public_ip, port):
    # todo: add name, ips and port checks

    host, cookies = get_node_creds(config)

    data = {
        'name': name,
    }

    url = construct_url(host, URLS['login'])
    response = requests.post(url, json=data)

    print(response)