import json
import inspect
import requests
import pickle
import urllib.parse
from cli.config import URLS, LONG_LINE
from cli.helper import safe_get_config, safe_load_texts

NODE_STATUSES = ['Not created', 'Requested', 'Active']
TEXTS = safe_load_texts()


def login_user(config, username, password):
    host = safe_get_config(config, 'host')
    if not host:
        return

    data = {
        'username': username,
        'password': password
    }
    url = urllib.parse.urljoin(host, URLS['login'])
    response = requests.post(url, json=data)

    if response.status_code == requests.codes.ok:
        cookies_text = pickle.dumps(response.cookies)
        config['cookies'] = cookies_text
        print('Success, cookies saved.')
    else:
        print('Authorization failed: ' + response.text)


def logout_user(config):
    host = safe_get_config(config, 'host')
    url = urllib.parse.urljoin(host, URLS['logout'])
    response = requests.get(url)

    if response.status_code == requests.codes.ok:
        clean_cookies(config)
        print('Cookies removed')
    else:
        print('Logout failed')
        print(response.text)


def clean_cookies(config):
    if safe_get_config(config, 'cookies'):
        del config["cookies"]


def test_host(host):
    url = urllib.parse.urljoin(host, URLS['test_host'])
    response = requests.get(url)
    return response.status_code == requests.codes.ok


def get_node_creds(config):
    host = safe_get_config(config, 'host')
    cookies_text = safe_get_config(config, 'cookies')
    if not host or not cookies_text:
        raise Exception(TEXTS['service']['no_node_host'])
    return host, cookies_text


def get_node_info(config, format):
    host, cookies_text = get_node_creds(config)
    cookies = pickle.loads(cookies_text)

    url = urllib.parse.urljoin(host, URLS['node_info'])
    response = requests.get(url, cookies=cookies)

    if response.status_code == requests.codes.unauthorized:
        clean_cookies(config)
        print(TEXTS['service']['unauthorized'])

    if response.status_code == requests.codes.ok:
        node_info = json.loads(response.text)
        if node_info['data']['status'] == 0:
            print(TEXTS['service']['node_not_registered'])
        else:
            if format == 'json':
                print(node_info)
            else:
                print_node_info(node_info)


def get_node_status(status):
    return NODE_STATUSES[status]


def print_node_info(node):
    print(inspect.cleandoc(f'''
        {LONG_LINE}
        Node info
        Name: {node['name']}
        IP: {node['ip']}
        Public IP: {node['publicIP']}
        Port: {node['port']}
        Status: {get_node_status(int(node['status']))}
        {LONG_LINE}
    '''))
