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
import stat
import logging
import shutil
import secrets

import urllib.request
from shutil import copyfile
from distutils.dir_util import copy_tree

from node_cli.configs import (
    CONTRACTS_PATH, BACKUP_CONTRACTS_PATH,
    MANAGER_CONTRACTS_FILEPATH, IMA_CONTRACTS_FILEPATH, SRC_FILEBEAT_CONFIG_PATH,
    FILESTORAGE_INFO_FILE, FILESTORAGE_ARTIFACTS_FILE, FILEBEAT_CONFIG_PATH, FLASK_SECRET_KEY_FILE
)
from node_cli.utils.helper import read_json


logger = logging.getLogger(__name__)


def backup_old_contracts():
    logging.info('Copying old contracts ABIs')
    copy_tree(CONTRACTS_PATH, BACKUP_CONTRACTS_PATH)


def download_contracts(env):
    urllib.request.urlretrieve(env['MANAGER_CONTRACTS_ABI_URL'], MANAGER_CONTRACTS_FILEPATH)
    urllib.request.urlretrieve(env['IMA_CONTRACTS_ABI_URL'], IMA_CONTRACTS_FILEPATH)


def download_filestorage_artifacts():
    logger.info('Updating filestorage artifacts')
    fs_artifacts_url = read_json(FILESTORAGE_INFO_FILE)['artifacts_url']
    logger.debug(f'Downloading {fs_artifacts_url} to {FILESTORAGE_ARTIFACTS_FILE}')
    urllib.request.urlretrieve(fs_artifacts_url, FILESTORAGE_ARTIFACTS_FILE)


def configure_filebeat():
    logger.info('Configuring filebeat...')
    copyfile(SRC_FILEBEAT_CONFIG_PATH, FILEBEAT_CONFIG_PATH)
    shutil.chown(FILEBEAT_CONFIG_PATH, user='root')
    os.chmod(
        FILEBEAT_CONFIG_PATH,
        stat.S_IREAD |
        stat.S_IWRITE |
        stat.S_IEXEC
    )
    logger.info('Filebeat configured')


def configure_flask():
    if os.path.isfile(FLASK_SECRET_KEY_FILE):
        logger.info('Flask secret key already exists')
    else:
        logger.info('Generating Flask secret key...')
        flask_secret_key = secrets.token_urlsafe(16)
        with open(FLASK_SECRET_KEY_FILE, 'w') as f:
            f.write(flask_secret_key)
        logger.info('Flask secret key generated and saved')
