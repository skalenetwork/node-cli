import os
import logging
import subprocess
import requests
from urllib.parse import urlparse

from core.resources import save_resource_allocation_config

from core.config import DEPENDENCIES_SCRIPT, URLS, SKALE_NODE_UI_PORT, DEFAULT_URL_SCHEME, \
    INSTALL_CONVOY_SCRIPT
from configs.node import NODE_DATA_PATH
from configs.cli_logger import LOG_DATA_PATH
from configs.resource_allocation import DISK_MOUNTPOINT_FILEPATH, \
    CONVOY_HELPER_SCRIPT_FILEPATH, CONVOY_SERVICE_TEMPLATE_PATH, CONVOY_SERVICE_PATH

from core.helper import safe_get_config, safe_load_texts, construct_url, clean_cookies, clean_host, get_localhost_endpoint
from tools.helper import run_cmd, process_template, get_username

TEXTS = safe_load_texts()

logger = logging.getLogger(__name__)

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


def reset_host(config):
    clean_cookies(config)
    clean_host(config)
    logging.info(f'Resetting host to defaut: {get_localhost_endpoint()}')
    print('Host removed, cookies cleaned.')


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


def prepare_host(test_mode, disk_mountpoint):
    logger.info(f'Preparing host started, disk_mountpoint: {disk_mountpoint}')
    save_disk_mountpoint(disk_mountpoint)
    save_resource_allocation_config()
    if not test_mode:
        init_convoy(disk_mountpoint)

def init_convoy(disk_mountpoint):
    print(f'Installing convoy...')
    run_cmd(['bash', INSTALL_CONVOY_SCRIPT], shell=False)
    print(f'Downloading convoy disk helper...')
    convoy_prepare_disk(disk_mountpoint)
    start_convoy_daemon(disk_mountpoint)


def start_convoy_daemon(disk_mountpoint):
    template_data = {
        #'user': get_username(),
        'cmd': f'/usr/local/bin/convoy daemon --drivers devicemapper --driver-opts dm.datadev={disk_mountpoint}1 --driver-opts dm.metadatadev={disk_mountpoint}2'
    }
    msg = f'Starting convoy daemon, template data: {template_data}'
    logger.info(msg), print(msg)
    process_template(CONVOY_SERVICE_TEMPLATE_PATH, CONVOY_SERVICE_PATH, template_data)
    run_cmd(['systemctl', 'enable', 'convoy'], shell=False)
    run_cmd(['systemctl', 'start', 'convoy'], shell=False)


def convoy_prepare_disk(disk_mountpoint):
    msg = 'Applying disk partitioning...'
    logger.info(msg), print(msg)
    run_cmd(['bash', CONVOY_HELPER_SCRIPT_FILEPATH, '--write-to-disk', f'{disk_mountpoint}'],
            shell=False)


def save_disk_mountpoint(disk_mountpoint):
    logger.info(f'Saving disk_mountpoint option to {DISK_MOUNTPOINT_FILEPATH}')
    with open(DISK_MOUNTPOINT_FILEPATH, 'w') as f:
        f.write(disk_mountpoint)


def init_data_dir():
    if os.path.exists(LOG_DATA_PATH):
        return
    msg = f'Creating {NODE_DATA_PATH} directory...'
    logger.info(msg), print(msg)
    os.makedirs(NODE_DATA_PATH, exist_ok=True)
    os.makedirs(LOG_DATA_PATH, exist_ok=True)
