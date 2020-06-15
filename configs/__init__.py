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
import sys
from pathlib import Path
from configs.routes import ROUTES  # noqa: F401

HOME_DIR = str(Path.home())
SKALE_DIR = os.path.join(HOME_DIR, '.skale')

NODE_DATA_PATH = os.path.join(SKALE_DIR, 'node_data')
CONTAINER_CONFIG_PATH = os.path.join(SKALE_DIR, 'config')
CONTRACTS_PATH = os.path.join(SKALE_DIR, 'contracts_info')

LOG_PATH = os.path.join(SKALE_DIR, NODE_DATA_PATH, 'log')
NODE_CERTS_PATH = os.path.join(SKALE_DIR, NODE_DATA_PATH, 'ssl')
SGX_CERTS_PATH = os.path.join(NODE_DATA_PATH, 'sgx_certs')
SCHAINS_DATA_PATH = os.path.join(NODE_DATA_PATH, 'schains')

CONFIG_FILEPATH = os.environ.get('CONFIG_FILEPATH') or \
                              os.path.join(SKALE_DIR, '.skale-cli.yaml')

TOKENS_FILEPATH = os.path.join(NODE_DATA_PATH, 'tokens.json')

CURRENT_FILE_LOCATION = os.path.dirname(os.path.realpath(__file__))
DOTENV_FILEPATH = os.path.join(os.path.dirname(CURRENT_FILE_LOCATION), '.env')


def _get_env():
    try:
        sys._MEIPASS
    except AttributeError:
        return 'dev'
    return 'prod'


ENV = _get_env()
CURRENT_FILE_LOCATION = os.path.dirname(os.path.realpath(__file__))

if ENV == 'dev':
    PARDIR = os.path.join(CURRENT_FILE_LOCATION, os.pardir)
else:
    PARDIR = os.path.join(sys._MEIPASS, 'data')

TEXT_FILE = os.path.join(PARDIR, 'text.yml')
DATAFILES_FOLDER = os.path.join(PARDIR, 'datafiles')

THIRDPARTY_FOLDER_PATH = os.path.join(DATAFILES_FOLDER, 'third_party')

DEPENDENCIES_SCRIPT = os.path.join(DATAFILES_FOLDER, 'dependencies.sh')
INSTALL_SCRIPT = os.path.join(DATAFILES_FOLDER, 'install.sh')
BACKUP_INSTALL_SCRIPT = os.path.join(DATAFILES_FOLDER, 'backup-install.sh')
UNINSTALL_SCRIPT = os.path.join(DATAFILES_FOLDER, 'uninstall.sh')
UPDATE_SCRIPT = os.path.join(DATAFILES_FOLDER, 'update.sh')

ALLOCATION_FILEPATH = os.path.join(DATAFILES_FOLDER, 'allocation.yml')

LONG_LINE = '-' * 50

ADMIN_PORT = 3007
ADMIN_HOST = 'localhost'
DEFAULT_URL_SCHEME = 'http://'

DEFAULT_NODE_BASE_PORT = 10000

BACKUP_ARCHIVE_NAME = 'skale-node-backup'
