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

import sys
import os
import platform
from pathlib import Path

ENV = os.environ.get('ENV')

home = str(Path.home())

CONFIG_FILEPATH = os.environ.get('CONFIG_FILEPATH', None) or \
                  os.path.join(home, '.skale-cli.yaml')

CURRENT_FILE_LOCATION = os.path.dirname(os.path.realpath(__file__))

if ENV == 'dev':
    PARDIR = os.path.join(CURRENT_FILE_LOCATION, os.pardir)
else:
    PARDIR = os.path.join(sys._MEIPASS, 'data')

TEXT_FILE = os.path.join(PARDIR, 'text.yml')
DATAFILES_FOLDER = os.path.join(PARDIR, 'datafiles')

THIRDPARTY_FOLDER_NAME = 'third_party'
THIRDPARTY_FOLDER_PATH = os.path.join(DATAFILES_FOLDER, THIRDPARTY_FOLDER_NAME)

DEPENDENCIES_SCRIPT = os.path.join(DATAFILES_FOLDER, 'dependencies.sh')
INSTALL_SCRIPT = os.path.join(DATAFILES_FOLDER, 'install.sh')
INSTALL_CONVOY_SCRIPT = os.path.join(DATAFILES_FOLDER, 'install_convoy.sh')
UPDATE_NODE_PROJECT_SCRIPT = os.path.join(DATAFILES_FOLDER, 'update_node_project.sh')

URLS = {
    'login': '/login',
    'logout': '/logout',
    'register': '/join',
    'node_info': '/node-info',
    'node_about': '/about-node',
    'create_node': '/create-node',
    'test_host': '/test-host',

    'wallet_info': '/load-wallet',
    'validators_info': '/validators-info',

    'schains_containers': '/containers/schains/list',
    'node_schains': '/schains/list',
    'schain_config': '/schain-config',
    'skale_containers': '/containers/list',

    'logs_dump': '/logs/dump',
    'first-bounties': '/first-bounties',
    'last-bounties': '/last-bounties'
}

LONG_LINE = '-' * 50

SKALE_NODE_UI_PORT = 3007
SKALE_NODE_UI_LOCALHOST = 'http://0.0.0.0'
DEFAULT_URL_SCHEME = 'http://'

SKALE_PROJECT_PATH = os.path.join('/skale', 'skale-node')
UNINSTALL_SCRIPT = os.path.join(SKALE_PROJECT_PATH, 'scripts', 'uninstall.sh')
UPDATE_SCRIPT = os.path.join(SKALE_PROJECT_PATH, 'scripts', 'update.sh')

NODE_DATA_PATH = '/skale_node_data'
TOKENS_FILENAME = 'tokens.json'
TOKENS_FILEPATH = os.path.join(NODE_DATA_PATH, TOKENS_FILENAME)

DEFAULT_DB_USER = 'root'
DEFAULT_DB_PORT = '3306'

HOST_OS = platform.system()
MAC_OS_SYSTEM_NAME = 'Darwin'
