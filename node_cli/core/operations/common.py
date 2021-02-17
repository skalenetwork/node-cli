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
import logging

import urllib.request
from distutils.dir_util import copy_tree

from node_cli.core.operations.git_helper import update_repo
from node_cli.utils.docker_utils import (rm_all_schain_containers, rm_all_ima_containers,
                                         compose_pull, compose_build)
from node_cli.configs import (
    CONTRACTS_PATH, BACKUP_CONTRACTS_PATH,
    MANAGER_CONTRACTS_FILEPATH, IMA_CONTRACTS_FILEPATH, DOCKER_LVMPY_PATH,
    CONTAINER_CONFIG_PATH, FILESTORAGE_INFO_FILE, FILESTORAGE_ARTIFACTS_FILE
)
from node_cli.utils.helper import run_cmd, read_json

logger = logging.getLogger(__name__)


def remove_dynamic_containers():
    logger.info(f'Removing sChains containers')
    rm_all_schain_containers()
    logger.info(f'Removing IMA containers')
    rm_all_ima_containers()


def backup_old_contracts():
    logging.info('Copying old contracts ABIs')
    copy_tree(CONTRACTS_PATH, BACKUP_CONTRACTS_PATH)


def download_contracts(env):
    urllib.request.urlretrieve(env['MANAGER_CONTRACTS_ABI_URL'], MANAGER_CONTRACTS_FILEPATH)
    urllib.request.urlretrieve(env['IMA_CONTRACTS_ABI_URL'], IMA_CONTRACTS_FILEPATH)


def docker_lvmpy_update(env):
    update_repo(DOCKER_LVMPY_PATH, env["DOCKER_LVMPY_STREAM"])
    logging.info('Running docker-lvmpy update script')
    env['PHYSICAL_VOLUME'] = env['DISK_MOUNTPOINT']
    env['VOLUME_GROUP'] = 'schains'
    env['PATH'] = os.environ.get('PATH', None)
    run_cmd(
        cmd=f'sudo -H -E {DOCKER_LVMPY_PATH}/scripts/update.sh'.split(),
        env=env
    )
    logging.info('docker-lvmpy update done')


def download_filestorage_artifacts():
    logger.info(f'Updating filestorage artifacts')
    fs_artifacts_url = read_json(FILESTORAGE_INFO_FILE)['artifacts_url']
    logger.debug(f'Downloading {fs_artifacts_url} to {FILESTORAGE_ARTIFACTS_FILE}')
    urllib.request.urlretrieve(fs_artifacts_url, FILESTORAGE_ARTIFACTS_FILE)


def update_skale_node(env):
    if 'CONTAINER_CONFIGS_DIR' in env:
        update_skale_node_dev(env)
    else:
        update_skale_node_git(env)


def update_skale_node_git(env):
    update_repo(CONTAINER_CONFIG_PATH, env["CONTAINER_CONFIGS_STREAM"])
    compose_pull()


def update_skale_node_dev(env):
    sync_skale_node_dev(env)
    compose_build()


def sync_skale_node_dev(env):
    logger.info(f'Syncing {CONTAINER_CONFIG_PATH} with {env["CONTAINER_CONFIGS_DIR"]}')
    run_cmd(
        cmd=f'rsync -r {env["CONTAINER_CONFIGS_DIR"]}/ {CONTAINER_CONFIG_PATH}'.split()
    )
    run_cmd(
        cmd=f'rsync -r {env["CONTAINER_CONFIGS_DIR"]}/.git {CONTAINER_CONFIG_PATH}'.split()
    )
