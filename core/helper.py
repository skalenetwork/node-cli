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
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

import json
import os
import re
import shutil
from functools import wraps
import urllib.parse

import logging
import logging.handlers as py_handlers
from logging import Formatter

import requests
import yaml

from configs import TEXT_FILE, ADMIN_HOST, ADMIN_PORT, LONG_LINE, ROUTES
from configs.cli_logger import (LOG_FORMAT, LOG_BACKUP_COUNT,
                                LOG_FILE_SIZE_BYTES,
                                LOG_FILEPATH, DEBUG_LOG_FILEPATH)
from tools.helper import session_config


config = session_config()
logger = logging.getLogger(__name__)


HOST = f'http://{ADMIN_HOST}:{ADMIN_PORT}'


def safe_get_config(config, key):
    try:
        return config[key]
    except KeyError as e:
        logger.error(e)
        # print(f'No such key in config: {key}')
        return None


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


def construct_url(route):
    return urllib.parse.urljoin(HOST, route)


def get_response_data(response):
    json = response.json()
    return json['data']


def abort_if_false(ctx, param, value):
    if not value:
        ctx.abort()


def get_request(url, params=None):
    try:
        return requests.get(url, params=params)
    except requests.exceptions.ConnectionError as e:
        logger.error(e)
        print(f'Could not connect to {url}')
        return None


def post_request(url, json=None, files=None):
    try:
        return requests.post(url, json=json, files=files)
    except requests.exceptions.ConnectionError as e:
        logger.error(e)
        print(f'Could not connect to {url}')
        return None


def print_err_response(err_response):
    print(LONG_LINE)
    for error in err_response['errors']:
        print(error)
    print(LONG_LINE)


def post(url_name, json=None, files=None):
    url = construct_url(ROUTES[url_name])
    response = post_request(url, json=json, files=files)
    if response is None:
        return None
    try:
        json_data = response.json()
    except Exception as err:
        logger.error('Response parsing failed', exc_info=err)
        return {'errors': ['Response parsing failed. Check skale_admin container logs']}
    return json_data


def get(url_name, params=None):
    url = construct_url(ROUTES[url_name])

    response = get_request(url, params)
    if response is None:
        return None

    if response.status_code != requests.codes.ok:  # pylint: disable=no-member
        print('Request failed, status code:', response.status_code)
        return None

    try:
        json = response.json()
    except Exception as err:
        logger.error('Response parsing failed', exc_info=err)
        return {'errors': 'Response parsing failed. Check skale_admin container logs'}

    if json['res'] != 1:
        print_err_response(response.json())
        return None
    else:
        return json['data']


def download_dump(path, container_name=None):
    url = construct_url(ROUTES['logs_dump'])
    params = {}
    if container_name:
        params['container_name'] = container_name
    with requests.get(url, params=params, stream=True) as r:
        if r is None:
            return None
        if r.status_code != requests.codes.ok:  # pylint: disable=no-member
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


def load_ssl_files(key_path, cert_path):
    return {
        'ssl_key': (os.path.basename(key_path), read_file(key_path), 'application/octet-stream'),
        'ssl_cert': (os.path.basename(cert_path), read_file(cert_path), 'application/octet-stream')
    }


def read_file(path, mode='rb'):
    with open(path, mode) as f:
        return f


def upload_certs(key_path, cert_path, force):
    with open(key_path, 'rb') as key_file, open(cert_path, 'rb') as cert_file:
        files_data = {
            'ssl_key': (os.path.basename(key_path), key_file,
                        'application/octet-stream'),
            'ssl_cert': (os.path.basename(cert_path), cert_file,
                         'application/octet-stream')
        }
        files_data['json'] = (
            None, json.dumps({'force': force}),
            'application/json'
        )
        return post('ssl_upload', files=files_data)
