#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
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
import sys

import yaml
import shutil
import requests
import subprocess
import urllib.request

import urllib.parse
from functools import wraps

import logging
from logging import Formatter, StreamHandler
import logging.handlers as py_handlers

import distutils
import distutils.util

import click

from jinja2 import Environment

from node_cli.utils.print_formatters import print_err_response
from node_cli.utils.exit_codes import CLIExitCodes
from node_cli.configs.env import (
    absent_params as absent_env_params,
    get_params as get_env_params
)
from node_cli.configs import (
    TEXT_FILE, ADMIN_HOST, ADMIN_PORT, HIDE_STREAM_LOG, GLOBAL_SKALE_DIR,
    GLOBAL_SKALE_CONF_FILEPATH
)
from node_cli.configs.routes import get_route
from node_cli.utils.global_config import read_g_config, get_system_user

from node_cli.configs.cli_logger import (
    FILE_LOG_FORMAT, LOG_BACKUP_COUNT, LOG_FILE_SIZE_BYTES,
    LOG_FILEPATH, STREAM_LOG_FORMAT, DEBUG_LOG_FILEPATH)


logger = logging.getLogger(__name__)


HOST = f'http://{ADMIN_HOST}:{ADMIN_PORT}'

DEFAULT_ERROR_DATA = {
    'status': 'error',
    'payload': 'Request failed. Check skale_api container logs'
}


def read_json(path):
    with open(path, encoding='utf-8') as data_file:
        return json.loads(data_file.read())


def write_json(path, content):
    with open(path, 'w') as outfile:
        json.dump(content, outfile, indent=4)


def run_cmd(cmd, env={}, shell=False, secure=False, check_code=True):
    if not secure:
        logger.debug(f'Running: {cmd}')
    else:
        logger.debug('Running some secure command')
    res = subprocess.run(cmd, shell=shell,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, env={**env, **os.environ})
    if check_code:
        output = res.stdout.decode('utf-8')
        if res.returncode:
            logger.error(f'Error during shell execution: {output}')
            res.check_returncode()
        else:
            logger.debug('Command is executed successfully. Command log:')
            logger.debug(res.stdout.decode('UTF-8').rstrip())
    return res


def format_output(res: subprocess.CompletedProcess) -> str:
    return res.stdout.decode('UTF-8').rstrip()


def download_file(url, filepath):
    return urllib.request.urlretrieve(url, filepath)


def process_template(source, destination, data):
    """
    :param source: j2 template source path
    :param destination: out file path
    :param data: dictionary with fields for template
    :return: Nothing
    """
    template = read_file(source)
    processed_template = Environment().from_string(template).render(data)
    with open(destination, "w") as f:
        f.write(processed_template)


def get_username():
    return os.environ.get('USERNAME') or os.environ.get('USER')


def extract_env_params(env_filepath):
    env_params = get_env_params(env_filepath)

    absent_params = ', '.join(absent_env_params(env_params))
    if absent_params:
        click.echo(f"Your env file({env_filepath}) have some absent params: "
                   f"{absent_params}.\n"
                   f"You should specify them to make sure that "
                   f"all services are working",
                   err=True)
        return None
    return env_params


def str_to_bool(val):
    return bool(distutils.util.strtobool(val))


def error_exit(error_payload, exit_code=CLIExitCodes.FAILURE):
    print_err_response(error_payload)
    sys.exit(exit_code.value)


def safe_get_config(config, key):
    try:
        return config[key]
    except KeyError as e:
        logger.error(e)
        return None


def safe_load_texts():
    with open(TEXT_FILE, 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)


def safe_load_yml(filepath):
    with open(filepath, 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)


def construct_url(route):
    return urllib.parse.urljoin(HOST, route)


def abort_if_false(ctx, param, value):
    if not value:
        ctx.abort()


def post_request(blueprint, method, json=None, files=None):
    route = get_route(blueprint, method)
    url = construct_url(route)
    try:
        response = requests.post(url, json=json, files=files)
        data = response.json()
    except Exception as err:
        logger.error('Request failed', exc_info=err)
        data = DEFAULT_ERROR_DATA
    status = data['status']
    payload = data['payload']
    return status, payload


def get_request(blueprint, method, params=None):
    route = get_route(blueprint, method)
    url = construct_url(route)
    try:
        response = requests.get(url, params=params)
        data = response.json()
    except Exception as err:
        logger.error('Request failed', exc_info=err)
        data = DEFAULT_ERROR_DATA

    status = data['status']
    payload = data['payload']
    return status, payload


def download_dump(path, container_name=None):
    route = get_route('logs', 'dump')
    url = construct_url(route)
    params = {}
    if container_name:
        params['container_name'] = container_name
    with requests.get(url, params=params, stream=True) as r:
        if r is None:
            return None
        if r.status_code != requests.codes.ok:  # pylint: disable=no-member
            print('Request failed, status code:', r.status_code)
            error_exit(r.json())
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
    logging.basicConfig(
        level=logging.DEBUG, handlers=[f_handler, debug_f_handler])


def get_stream_handler():
    formatter = Formatter(STREAM_LOG_FORMAT)
    stream_handler = StreamHandler(sys.stderr)
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.INFO)
    return stream_handler


def get_file_handler(log_filepath, log_level):
    formatter = Formatter(FILE_LOG_FORMAT)
    f_handler = py_handlers.RotatingFileHandler(
        log_filepath, maxBytes=LOG_FILE_SIZE_BYTES,
        backupCount=LOG_BACKUP_COUNT)
    f_handler.setFormatter(formatter)
    f_handler.setLevel(log_level)

    return f_handler


def read_file(path):
    file = open(path, 'r')
    text = file.read()
    file.close()
    return text


def to_camel_case(snake_str):
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def validate_abi(abi_filepath: str) -> dict:
    if not os.path.isfile(abi_filepath):
        return {'filepath': abi_filepath,
                'status': 'error',
                'msg': 'No such file'}
    try:
        with open(abi_filepath) as abi_file:
            json.load(abi_file)
    except Exception:
        return {'filepath': abi_filepath, 'status': 'error',
                'msg': 'Failed to load abi file as json'}
    return {'filepath': abi_filepath, 'status': 'ok', 'msg': ''}


def streamed_cmd(func):
    """ Decorator that allow function to print logs into stderr """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if HIDE_STREAM_LOG is None:
            logging.getLogger('').addHandler(get_stream_handler())
        return func(*args, **kwargs)
    return wrapper


def is_user_valid(allow_root=True):
    current_user = get_system_user()
    if current_user == 'root' and allow_root:
        return True
    g_conf_user = get_g_conf_user()
    return current_user == g_conf_user


def get_g_conf():
    return read_g_config(GLOBAL_SKALE_DIR, GLOBAL_SKALE_CONF_FILEPATH)


def get_g_conf_user():
    return get_g_conf()['user']


def get_g_conf_home():
    return get_g_conf()['home_dir']
