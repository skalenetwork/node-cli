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

import logging
import os.path

from node_cli.utils.docker_utils import restart_nginx_container, docker_client
from node_cli.configs import NODE_CERTS_PATH, NGINX_TEMPLATE_FILEPATH, NGINX_CONFIG_FILEPATH
from node_cli.utils.helper import process_template


logger = logging.getLogger(__name__)


SSL_KEY_NAME = 'ssl_key'
SSL_CRT_NAME = 'ssl_cert'


def generate_nginx_config() -> None:
    ssl_on = check_ssl_certs()
    template_data = {
        'ssl': ssl_on,
    }
    logger.info(f'Processing nginx template. ssl: {ssl_on}')
    process_template(NGINX_TEMPLATE_FILEPATH, NGINX_CONFIG_FILEPATH, template_data)


def check_ssl_certs():
    crt_path = os.path.join(NODE_CERTS_PATH, SSL_CRT_NAME)
    key_path = os.path.join(NODE_CERTS_PATH, SSL_KEY_NAME)
    return os.path.exists(crt_path) and os.path.exists(key_path)


def reload_nginx() -> None:
    dutils = docker_client()
    generate_nginx_config()
    restart_nginx_container(dutils=dutils)
