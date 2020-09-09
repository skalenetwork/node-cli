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

import os
import json
import logging
import subprocess
import urllib.request
from subprocess import PIPE

import click

from jinja2 import Environment
from readsettings import ReadSettings

from configs.env import (absent_params as absent_env_params,
                         get_params as get_env_params)
from configs import CONFIG_FILEPATH

logger = logging.getLogger(__name__)


def read_json(path):
    with open(path, encoding='utf-8') as data_file:
        return json.loads(data_file.read())


def write_json(path, content):
    with open(path, 'w') as outfile:
        json.dump(content, outfile, indent=4)


def run_cmd(cmd, env={}, shell=False, secure=False):
    if not secure:
        logger.info(f'Running: {cmd}')
    else:
        logger.info(f'Running some secure command')
    res = subprocess.run(cmd, shell=shell, stdout=PIPE, stderr=PIPE, env={**env, **os.environ})
    if res.returncode:
        logger.error('Error during shell execution:')
        logger.error(res.stderr.decode('UTF-8').rstrip())
        raise subprocess.CalledProcessError(res.returncode, cmd)
    else:
        logger.info('Command is executed successfully. Command log:')
        logger.info(res.stdout.decode('UTF-8').rstrip())
    return res


def format_output(res):
    return res.stdout.decode('UTF-8').rstrip(), res.stderr.decode('UTF-8').rstrip()


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


def read_file(path):
    file = open(path, 'r')
    text = file.read()
    file.close()
    return text


def get_username():
    return os.environ.get('USERNAME') or os.environ.get('USER')


def session_config():
    return ReadSettings(CONFIG_FILEPATH)


def extract_env_params(env_filepath):
    env_params = get_env_params(env_filepath)
    if not env_params.get('DB_ROOT_PASSWORD'):
        env_params['DB_ROOT_PASSWORD'] = env_params['DB_PASSWORD']

    absent_params = ', '.join(absent_env_params(env_params))
    if absent_params:
        click.echo(f"Your env file({env_filepath}) have some absent params: "
                   f"{absent_params}.\n"
                   f"You should specify them to make sure that "
                   f"all services are working",
                   err=True)
        return None
    return env_params
