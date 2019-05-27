import json
import inspect
import requests
import pickle
from cli.config import URLS, LONG_LINE
from cli.helper import safe_get_config, safe_load_texts, get_node_creds, construct_url, get_response_data

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
    url = construct_url(host, URLS['login'])
    response = requests.post(url, json=data)

    if response.status_code == requests.codes.ok:
        cookies_text = pickle.dumps(response.cookies)
        config['cookies'] = cookies_text
        print('Success, cookies saved.')
    else:
        print('Authorization failed: ' + response.text)


def logout_user(config):
    host = safe_get_config(config, 'host')
    url = construct_url(host, URLS['logout'])
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
    url = construct_url(host, URLS['test_host'])

    try:
        response = requests.get(url)
    except requests.exceptions.ConnectionError:
        return False  # todo: return different error messages
    except requests.exceptions.InvalidURL:
        return False  # todo: return different error messages

    return response.status_code == requests.codes.ok


def get_node_info(config, format):
    host, cookies = get_node_creds(config)
    url = construct_url(host, URLS['node_info'])
    response = requests.get(url, cookies=cookies)

    if response.status_code == requests.codes.unauthorized:
        clean_cookies(config)
        print(TEXTS['service']['unauthorized'])
        return

    if response.status_code == requests.codes.ok:
        node_info = get_response_data(response)
        if node_info['status'] == 0:
            print(TEXTS['service']['node_not_registered'])
        else:
            if format == 'json':
                print(node_info)
            else:
                print_node_info(node_info)


def get_node_about(config, format):
    host, cookies = get_node_creds(config)
    url = construct_url(host, URLS['node_about'])
    response = requests.get(url, cookies=cookies)

    if response.status_code == requests.codes.unauthorized:
        clean_cookies(config)
        print(TEXTS['service']['unauthorized'])
        return

    if response.status_code == requests.codes.ok:
        node_about = get_response_data(response)
        print(node_about)

        # todo
        # if format == 'json':
        #     print(node_info)
        # else:
        #     print_node_info(node_info)


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
