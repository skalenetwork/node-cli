import os
import subprocess
import requests
from urllib.parse import urlparse
from core.config import DEPENDENCIES_SCRIPT, URLS, SKALE_NODE_UI_PORT, DEFAULT_URL_SCHEME
from core.helper import safe_get_config, safe_load_texts, construct_url

TEXTS = safe_load_texts()


def install_host_dependencies():
    env = {
        **os.environ,
        'SKALE_CMD': 'host_deps'
    }
    res = subprocess.run(["sudo", "bash", DEPENDENCIES_SCRIPT], env=env)
    # todo: check execution status


def show_host(config):
    host = safe_get_config(config, 'host')
    if host:
        print(f'SKALE node host: {host}')
    else:
        print(TEXTS['service']['no_node_host'])


def test_host(host):
    url = construct_url(host, URLS['test_host'])

    try:
        response = requests.get(url)
    except requests.exceptions.ConnectionError:
        return False  # todo: return different error messages
    except requests.exceptions.InvalidURL:
        return False  # todo: return different error messages

    return response.status_code == requests.codes.ok

def fix_url(url):
    try:
        result = urlparse(url)
        if not result.scheme:
            url = f'{DEFAULT_URL_SCHEME}{url}'
        if not url.endswith(str(SKALE_NODE_UI_PORT)):
            return f'{url}:{SKALE_NODE_UI_PORT}'
        return url
    except ValueError:
        return False