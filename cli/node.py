import requests
from cli.config import URLS
from cli.helper import get_node_creds, construct_url


def create_node(config, name, p2p_ip, public_ip, port):
    # todo: add name, ips and port checks
    host, cookies = get_node_creds(config)
    data = {
        'name': name,
        'ip': p2p_ip,
        'publicIP': public_ip,
        'port': port
    }
    url = construct_url(host, URLS['create_node'])
    response = requests.post(url, json=data, cookies=cookies)

    print(response.text)