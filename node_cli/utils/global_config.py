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

from node_cli.core.host import safe_mk_dirs
from node_cli.utils.helper import write_json, read_json
from node_cli.configs import GLOBAL_SKALE_CONF_FILEPATH, GLOBAL_SKALE_DIR


def read_g_config() -> dict:
    """Read global SKALE config file, init if not exists"""
    try:
        return read_json(GLOBAL_SKALE_CONF_FILEPATH)
    except FileNotFoundError:
        return generate_g_config_file()


def generate_g_config_file() -> dict:
    """Init global SKALE config file"""
    safe_mk_dirs(GLOBAL_SKALE_DIR)
    g_config = {
        'user': get_system_user(),
        'home_dir': os.path.expanduser('~')
    }
    write_json(GLOBAL_SKALE_CONF_FILEPATH, g_config)
    return g_config


def get_system_user() -> str:
    if os.getenv('SUDO_USER'):
        return os.environ['SUDO_USER']
    else:
        return os.environ['USER']


def is_user_valid(allow_root=True):
    current_user = get_system_user()
    if current_user == 'root' and allow_root:
        return True
    g_conf_user = get_g_conf_user()
    return current_user == g_conf_user


def get_g_conf_user():
    return read_g_config()['user']


def get_g_conf_home():
    return read_g_config()['home_dir']
