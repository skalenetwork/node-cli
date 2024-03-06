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
from typing import Optional

from node_cli.utils.helper import rm_dir, rsync_dirs, safe_mkdir
from node_cli.utils.git_utils import clone_repo
from node_cli.utils.docker_utils import compose_pull, compose_build
from node_cli.configs import (
    CONTAINER_CONFIG_PATH,
    CONTAINER_CONFIG_TMP_PATH,
    SKALE_NODE_REPO_URL
)


logger = logging.getLogger(__name__)


def update_images(local: bool = False, sync_node: bool = False) -> None:
    if local:
        compose_build(sync_node=sync_node)
    else:
        compose_pull(sync_node=sync_node)


def download_skale_node(stream: Optional[str], src: Optional[str]) -> None:
    rm_dir(CONTAINER_CONFIG_TMP_PATH)
    safe_mkdir(CONTAINER_CONFIG_TMP_PATH)
    dest = CONTAINER_CONFIG_TMP_PATH
    if src:
        rsync_dirs(src, dest)
    else:
        clone_repo(
            SKALE_NODE_REPO_URL,
            CONTAINER_CONFIG_TMP_PATH,
            stream
        )


def sync_skale_node():
    if os.path.isdir(CONTAINER_CONFIG_PATH):
        shutil.rmtree(CONTAINER_CONFIG_PATH)
    shutil.move(CONTAINER_CONFIG_TMP_PATH, f'{CONTAINER_CONFIG_PATH}/')
