import inspect
import requests
from core.config import URLS, LONG_LINE
from core.helper import safe_get_config, safe_load_texts, get_node_creds, construct_url, \
    get_response_data, clean_cookies, get_request

NODE_STATUSES = ['Not created', 'Requested', 'Active']
TEXTS = safe_load_texts()


def get_node_info(config, format):
    host, cookies = get_node_creds(config)
    url = construct_url(host, URLS['node_info'])
    response = get_request(url, cookies)
    if response is None:
        return None

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

    response = get_request(url, cookies)
    if response is None:
        return None

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