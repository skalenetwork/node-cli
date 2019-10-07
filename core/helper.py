#   -*- coding: utf-8 -*-
#
#   This file is part of skale-node-cli
#
#   Copyright (C) 2019 SKALE Labs
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

import pickle
import yaml
import os
import re
import requests
import shutil
from functools import wraps
import urllib.parse

import logging
import logging.handlers as py_handlers
from logging import Formatter

from core.config import TEXT_FILE, SKALE_NODE_UI_LOCALHOST, SKALE_NODE_UI_PORT, \
    LONG_LINE, URLS, HOST_OS, MAC_OS_SYSTEM_NAME
from configs.cli_logger import LOG_FORMAT, LOG_BACKUP_COUNT, LOG_FILE_SIZE_BYTES, LOG_FILEPATH, \
    DEBUG_LOG_FILEPATH
from tools.helper import session_config


config = session_config()
logger = logging.getLogger(__name__)


def safe_get_config(config, key):
    try:
        return config[key]
    except KeyError as e:
        logger.error(e)
        # print(f'No such key in config: {key}')
        return None


def cookies_exists():
    return safe_get_config(config, 'cookies') is not None


def login_required(f):
    @wraps(f)
    def inner(*args, **kwargs):
        if cookies_exists():
            return f(*args, **kwargs)
        else:
            TEXTS = safe_load_texts()
            print(TEXTS['service']['unauthorized'])

    return inner


def local_only(f):
    @wraps(f)
    def inner(*args, **kwargs):
        host = safe_get_config(config, 'host')
        if host:
            print('This command couldn\'t be executed on the remote SKALE host.')
        else:
            if HOST_OS == MAC_OS_SYSTEM_NAME:
                print('Sorry, local-only commands couldn\'t be executed on current OS.')
            else:
                return f(*args, **kwargs)

    return inner


def no_node(f):
    @wraps(f)
    def inner(*args, **kwargs):
        # todo: check that node is not installed yet!
        return f(*args, **kwargs)

    return inner


def safe_load_texts():
    with open(TEXT_FILE, 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)


def get_node_creds(config):
    TEXTS = safe_load_texts()
    host = safe_get_config(config, 'host')
    if not host:
        host = get_localhost_endpoint()
    cookies_text = safe_get_config(config, 'cookies')
    if not host or not cookies_text:
        raise Exception(TEXTS['service']['no_node_host'])
    cookies = pickle.loads(cookies_text)
    return host, cookies


def construct_url(host, url):
    return urllib.parse.urljoin(host, url)


def get_response_data(response):
    json = response.json()
    return json['data']


def clean_cookies(config):
    if safe_get_config(config, 'cookies'):
        del config["cookies"]


def clean_host(config):
    if safe_get_config(config, 'host'):
        del config['host']


def abort_if_false(ctx, param, value):
    if not value:
        ctx.abort()


def get_localhost_endpoint():
    return f'{SKALE_NODE_UI_LOCALHOST}:{SKALE_NODE_UI_PORT}'


def get_request(url, cookies=None, params=None):
    try:
        return requests.get(url, cookies=cookies, params=params)
    except requests.exceptions.ConnectionError as e:
        logger.error(e)
        print(f'Could not connect to {url}')
        return None


def post_request(url, json, cookies=None):
    try:
        return requests.post(url, json=json, cookies=cookies)
    except requests.exceptions.ConnectionError as e:
        logger.error(e)
        print(f'Could not connect to {url}')
        return None


def print_err_response(err_response):
    print(LONG_LINE)
    for error in err_response['errors']:
        print(error)
    print(LONG_LINE)


def get(url_name, params=None):
    host, cookies = get_node_creds(config)
    url = construct_url(host, URLS[url_name])

    response = get_request(url, cookies, params)
    if response is None:
        return None

    if response.status_code != requests.codes.ok:
        print('Request failed, status code:', response.status_code)
        return None

    json = response.json()
    if json['res'] != 1:
        print_err_response(response.json())
        return None
    else:
        return json['data']


def download_log_file(name, type, schain):
    host, cookies = get_node_creds(config)
    url = construct_url(host, URLS['log_download'])
    params = {
        'filename': name,
        'type': type,
        'schain_name': schain
    }

    local_filename = f'{schain}_{name}' if schain else name
    with requests.get(url, params=params, cookies=cookies, stream=True) as r:
        if r is None:
            return None
        if r.status_code != requests.codes.ok:
            print('Request failed, status code:', r.status_code)
            return None
        with open(local_filename, 'wb') as f:
            shutil.copyfileobj(r.raw, f)
    return local_filename


def download_dump(path, container_name=None):
    host, cookies = get_node_creds(config)
    url = construct_url(host, URLS['logs_dump'])
    params = {}
    if container_name:
        params['container_name'] = container_name
    with requests.get(url, params=params, cookies=cookies, stream=True) as r:
        if r is None:
            return None
        if r.status_code != requests.codes.ok:
            print('Request failed, status code:', r.status_code)
            print_err_response(r.json())
            return None
        d = r.headers['Content-Disposition']
        fname_q = re.findall("filename=(.+)", d)[0]
        fname = fname_q.replace('"', '')
        filepath = os.path.join(path, fname)
        with open(filepath, 'wb') as f:
            shutil.copyfileobj(r.raw, f)
    return fname


def init_default_logger():
    f_handler = get_file_handler(LOG_FILEPATH, logging.INFO)
    debug_f_handler = get_file_handler(DEBUG_LOG_FILEPATH, logging.DEBUG)
    logging.basicConfig(level=logging.DEBUG, handlers=[f_handler, debug_f_handler])


def get_file_handler(log_filepath, log_level):
    formatter = Formatter(LOG_FORMAT)
    f_handler = py_handlers.RotatingFileHandler(log_filepath, maxBytes=LOG_FILE_SIZE_BYTES,
                                                backupCount=LOG_BACKUP_COUNT)
    f_handler.setFormatter(formatter)
    f_handler.setLevel(log_level)

    return f_handler
