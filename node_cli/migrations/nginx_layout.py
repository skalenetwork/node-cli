#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
#
#   Copyright (C) 2026-Present SKALE Labs
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

from node_cli.configs import LEGACY_NGINX_CONFIG_FILEPATH

logger = logging.getLogger(__name__)

LEGACY_NGINX_BACKUP_FILEPATH = f'{LEGACY_NGINX_CONFIG_FILEPATH}.bak'


def migrate_nginx_layout() -> None:
    """Move the single-file nginx config aside, node_data/nginx/ replaces it"""
    if os.path.isfile(LEGACY_NGINX_CONFIG_FILEPATH):
        logger.info('Moving %s to %s', LEGACY_NGINX_CONFIG_FILEPATH, LEGACY_NGINX_BACKUP_FILEPATH)
        os.replace(LEGACY_NGINX_CONFIG_FILEPATH, LEGACY_NGINX_BACKUP_FILEPATH)
