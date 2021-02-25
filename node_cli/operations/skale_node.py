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

from node_cli.utils.helper import run_cmd
from node_cli.utils.git_utils import sync_repo
from node_cli.utils.docker_utils import compose_pull, compose_build
from node_cli.configs import CONTAINER_CONFIG_PATH, SKALE_NODE_REPO_URL


logger = logging.getLogger(__name__)


def sync_skale_node(env):
    if 'CONTAINER_CONFIGS_DIR' in env:
        sync_skale_node_dev(env)
    else:
        sync_skale_node_git(env)


def sync_skale_node_git(env):
    sync_repo(SKALE_NODE_REPO_URL, CONTAINER_CONFIG_PATH, env["CONTAINER_CONFIGS_STREAM"])
    compose_pull()


def sync_skale_node_dev(env):
    logger.info(f'Syncing {CONTAINER_CONFIG_PATH} with {env["CONTAINER_CONFIGS_DIR"]}')
    run_cmd(f'rsync -r {env["CONTAINER_CONFIGS_DIR"]}/ {CONTAINER_CONFIG_PATH}'.split())
    run_cmd(f'rsync -r {env["CONTAINER_CONFIGS_DIR"]}/.git {CONTAINER_CONFIG_PATH}'.split())
    compose_build()
