#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
#
#   Copyright (C) 2022-Present SKALE Labs
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

import os
import shutil
import logging
import subprocess
from contextlib import contextmanager
from node_cli.configs.ssl import SSL_CERT_FILEPATH, SSL_KEY_FILEPATH, SSL_FOLDER_PATH


logger = logging.getLogger(__name__)


def copy_cert_key_pair(cert, key):
    shutil.copyfile(cert, SSL_CERT_FILEPATH)
    shutil.copyfile(key, SSL_KEY_FILEPATH)


def cert_from_file(cert_filepath):
    if not os.path.isfile(cert_filepath):
        return None
    with open(cert_filepath) as cert_file:
        return cert_file.read()


def is_ssl_folder_empty(ssl_path=SSL_FOLDER_PATH):
    return len(os.listdir(ssl_path)) == 0


@contextmanager
def detached_subprocess(cmd, expose_output=False):
    logger.debug(f'Starting detached subprocess: {cmd}')
    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        encoding='utf-8'
    )
    try:
        yield p
    finally:
        p.terminate()
        output = p.stdout.read()
        if expose_output:
            print(output)
        logger.debug(f'Detached process {cmd} output:\n{output}')
