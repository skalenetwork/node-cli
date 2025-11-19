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

import distutils
import distutils.util
import ipaddress
import json
import logging
import logging.handlers as py_handlers
import os
import re
import shutil
import socket
import subprocess
import sys
import urllib.parse
import urllib.request
import uuid
from functools import wraps
from logging import Formatter, StreamHandler
from typing import Any, NoReturn, Optional
from urllib.parse import urlparse

import click
import requests
import yaml
from jinja2 import Environment

from node_cli.configs import (
    ADMIN_HOST,
    ADMIN_PORT,
    DEFAULT_SSH_PORT,
    GLOBAL_SKALE_CONF_FILEPATH,
    GLOBAL_SKALE_DIR,
    HIDE_STREAM_LOG,
)
from node_cli.configs.cli_logger import (
    DEBUG_LOG_FILEPATH,
    FILE_LOG_FORMAT,
    LOG_BACKUP_COUNT,
    LOG_FILE_SIZE_BYTES,
    LOG_FILEPATH,
    STREAM_LOG_FORMAT,
)
from node_cli.configs.routes import get_route
from node_cli.utils.exit_codes import CLIExitCodes
from node_cli.utils.global_config import get_system_user, read_g_config
from node_cli.utils.print_formatters import print_err_response

logger = logging.getLogger(__name__)

HOST = f'http://{ADMIN_HOST}:{ADMIN_PORT}'

DEFAULT_ERROR_DATA = {
    'status': 'error',
    'payload': 'Request failed. Check API container logs',
}


class InvalidEnvFileError(Exception):
    pass


def read_json(path: str) -> dict:
    with open(path, encoding='utf-8') as data_file:
        return json.loads(data_file.read())


def write_json(path: str, content: dict) -> None:
    with open(path, 'w') as outfile:
        json.dump(content, outfile, indent=4)


def save_json(path: str, content: dict) -> None:
    tmp_path = get_tmp_path(path)
    write_json(tmp_path, content)
    shutil.move(tmp_path, path)


def init_file(path, content=None):
    if not os.path.exists(path):
        write_json(path, content)


def run_cmd(cmd, env={}, shell=False, secure=False, check_code=True, separate_stderr=False):
    if not secure:
        logger.debug(f'Running: {cmd}')
    else:
        logger.debug('Running some secure command')
    stdout, stderr = subprocess.PIPE, subprocess.PIPE
    if not separate_stderr:
        stderr = subprocess.STDOUT
    res = subprocess.run(cmd, shell=shell, stdout=stdout, stderr=stderr, env={**env, **os.environ})
    if check_code:
        output = res.stdout.decode('utf-8')
        if res.returncode:
            if separate_stderr:
                output = res.stderr.decode('utf-8')
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
    with open(destination, 'w') as f:
        f.write(processed_template)


def get_username():
    return os.environ.get('USERNAME') or os.environ.get('USER')


def str_to_bool(val):
    return bool(distutils.util.strtobool(val))


def error_exit(error_payload: Any, exit_code: CLIExitCodes = CLIExitCodes.FAILURE) -> NoReturn:
    """Print error message and exit the program with specified exit code.

    Args:
        error_payload: Error message string or list of error messages
        exit_code: Exit code to use when terminating the program (default: FAILURE)

    Raises:
        TypeError: If exit_code is not CLIExitCodes

    Example:
        >>> error_exit("Permission denied", CLIExitCodes.BAD_USER_ERROR)
        Permission denied
        <exits with code 3>
    """
    if not isinstance(exit_code, CLIExitCodes):
        raise TypeError('exit_code must be CLIExitCodes enum')

    print_err_response(error_payload)
    sys.exit(exit_code.value)


def safe_get_config(config, key):
    try:
        return config[key]
    except KeyError as e:
        logger.error(e)
        return None


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
        logger.exception('Request failed', exc_info=err)
        data = DEFAULT_ERROR_DATA
    status = data['status']
    payload = data['payload']
    return status, payload


def get_request(
    blueprint: str, method: str, params: Optional[dict] = None
) -> tuple[str, str | dict]:
    route = get_route(blueprint, method)
    url = construct_url(route)
    try:
        response = requests.get(url, params=params)
        data = response.json()
    except Exception as err:
        logger.exception('Request failed', exc_info=err)
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
        fname_q = re.findall('filename=(.+)', d)[0]
        fname = fname_q.replace('"', '')
        filepath = os.path.join(path, fname)
        with open(filepath, 'wb') as f:
            shutil.copyfileobj(r.raw, f)
    return fname


def init_default_logger():
    f_handler = get_file_handler(LOG_FILEPATH, logging.INFO)
    debug_f_handler = get_file_handler(DEBUG_LOG_FILEPATH, logging.DEBUG)
    logging.basicConfig(level=logging.DEBUG, handlers=[f_handler, debug_f_handler])


def get_stream_handler():
    formatter = Formatter(STREAM_LOG_FORMAT)
    stream_handler = StreamHandler(sys.stderr)
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.INFO)
    return stream_handler


def get_file_handler(log_filepath, log_level):
    formatter = Formatter(FILE_LOG_FORMAT)
    f_handler = py_handlers.RotatingFileHandler(
        log_filepath, maxBytes=LOG_FILE_SIZE_BYTES, backupCount=LOG_BACKUP_COUNT
    )
    f_handler.setFormatter(formatter)
    f_handler.setLevel(log_level)

    return f_handler


def read_file(path):
    with open(path, 'r') as file:
        return file.read()


def to_camel_case(snake_str):
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def streamed_cmd(func):
    """Decorator that allows function to print logs into stderr."""

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


def rm_dir(folder: str) -> None:
    if os.path.exists(folder):
        logger.info(f'{folder} exists, removing...')
        shutil.rmtree(folder)
    else:
        logger.info(f"{folder} doesn't exist, skipping...")


def cleanup_dir_content(folder: str) -> None:
    if os.path.exists(folder):
        logger.info('Removing contents of %s', folder)
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)


def safe_mkdir(path: str, print_res: bool = False) -> None:
    if os.path.exists(path):
        logger.debug(f'Directory {path} already exists')
        return

    msg = f'Creating {path} directory...'
    logger.info(msg)
    if print_res:
        print(msg)

    os.makedirs(path, exist_ok=True)


def rsync_dirs(src: str, dest: str) -> None:
    logger.info(f'Syncing directory {dest} with {src}')

    try:
        run_cmd(['rsync', '-r', f'{src}/', dest])
        run_cmd(['rsync', '-r', f'{src}/.git', dest])
    except subprocess.CalledProcessError as e:
        logger.error(f'Rsync failed: {e}')
        error_exit(
            f'Failed to sync directories: {e}', exit_code=CLIExitCodes.OPERATION_EXECUTION_ERROR
        )


def ok_result(payload: dict = None):
    return 'ok', payload


def err_result(msg: str = None):
    return 'error', msg


class UrlType(click.ParamType):
    name = 'url'

    def convert(self, value, param, ctx):
        try:
            result = urlparse(value)
        except ValueError:
            self.fail(f'Some characters are not allowed in {value}', param, ctx)
        if not all([result.scheme, result.netloc]):
            self.fail(f'Expected valid url. Got {value}', param, ctx)
        return value


class UrlOrAnyType(UrlType):
    name = 'url'

    def convert(self, value, param, ctx):
        if value == 'any':
            return value
        return super().convert(value, param, ctx)


class IpType(click.ParamType):
    name = 'ip'

    def convert(self, value, param, ctx):
        try:
            ipaddress.ip_address(value)
        except ValueError:
            self.fail(f'expected valid ipv4/ipv6 address. Got {value}', param, ctx)
        return value


URL_TYPE = UrlType()
URL_OR_ANY_TYPE = UrlOrAnyType()
IP_TYPE = IpType()


def get_tmp_path(path: str) -> str:
    base, ext = os.path.splitext(path)
    salt = uuid.uuid4().hex[:5]
    return base + salt + '.tmp' + ext


def get_ssh_port(ssh_service_name='ssh'):
    try:
        return socket.getservbyname(ssh_service_name)
    except OSError:
        logger.exception('Cannot get ssh service port')
        return DEFAULT_SSH_PORT


def is_contract_address(value: str) -> bool:
    return bool(re.fullmatch(r'0x[a-fA-F0-9]{40}', value))


def is_btrfs_subvolume(path: str) -> bool:
    """Check if the given path is a Btrfs subvolume."""
    try:
        output = run_cmd(['btrfs', 'subvolume', 'show', path], check_code=False)
        return output.returncode == 0
    except subprocess.CalledProcessError:
        return False
