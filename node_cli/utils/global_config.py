#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
#
#   Copyright (C) 2021 SKALE Labs
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
import sys
import json
import logging

logger = logging.getLogger(__name__)


def get_system_user() -> str:
    return 'root' if get_home_dir() == '/root' else os.getenv('SUDO_USER', os.getenv('USER'))


def get_home_dir() -> str:
    return os.path.expanduser('~')


def read_g_config(g_skale_dir: str, g_skale_conf_filepath: str) -> dict:
    """Read global SKALE config file, init if not exists"""
    if not os.path.isfile(g_skale_conf_filepath):
        return generate_g_config_file(g_skale_dir, g_skale_conf_filepath)
    with open(g_skale_conf_filepath, encoding='utf-8') as data_file:
        return json.loads(data_file.read())


def generate_g_config_file(g_skale_dir: str, g_skale_conf_filepath: str) -> dict:
    """Init global SKALE config file"""
    print('Generating global SKALE config file...')
    os.makedirs(g_skale_dir, exist_ok=True)
    g_config = {
        'user': get_system_user(),
        'home_dir': get_home_dir()
    }
    print(f'{g_skale_conf_filepath} content: {g_config}')
    try:
        with open(g_skale_conf_filepath, 'w') as outfile:
            json.dump(g_config, outfile, indent=4)
    except PermissionError as e:
        logger.exception(e)
        print('No permissions to write into /etc directory')
        sys.exit(7)
    return g_config
