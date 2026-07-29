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

import logging
import os
import shutil
import stat
import tarfile
from shutil import copyfile

from node_cli.configs import (
    FILEBEAT_CONFIG_PATH,
    G_CONF_HOME,
    SRC_FILEBEAT_CONFIG_PATH,
)

logger = logging.getLogger(__name__)


def configure_filebeat():
    logger.info('Configuring filebeat...')
    copyfile(SRC_FILEBEAT_CONFIG_PATH, FILEBEAT_CONFIG_PATH)
    shutil.chown(FILEBEAT_CONFIG_PATH, user='root')
    os.chmod(FILEBEAT_CONFIG_PATH, stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC)
    logger.info('Filebeat configured')


def unpack_backup_archive(backup_path: str) -> None:
    logger.info('Unpacking backup archive...')
    with tarfile.open(backup_path) as tar:
        def is_within_directory(directory, target):
            
            abs_directory = os.path.abspath(directory)
            abs_target = os.path.abspath(target)
        
            prefix = os.path.commonprefix([abs_directory, abs_target])
            
            return prefix == abs_directory
        
        def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
        
            for member in tar.getmembers():
                member_path = os.path.join(path, member.name)
                if not is_within_directory(path, member_path):
                    raise Exception("Attempted Path Traversal in Tar File")
        
            tar.extractall(path, members, numeric_owner=numeric_owner) 
            
        
        safe_extract(tar, path=G_CONF_HOME)
