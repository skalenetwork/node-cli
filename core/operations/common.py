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

from time import sleep
import urllib.request
from distutils.dir_util import copy_tree

# from git.repo.base import Repo
from git.remote import Remote

from tools.docker_utils import rm_all_schain_containers, rm_all_ima_containers
from configs import (COMPOSE_PATH, CONTRACTS_PATH, BACKUP_CONTRACTS_PATH,
                     MANAGER_CONTRACTS_FILEPATH, IMA_CONTRACTS_FILEPATH, DOCKER_LVMPY_PATH)
from tools.helper import run_cmd

logger = logging.getLogger(__name__)


MAIN_COMPOSE_CONTAINERS = 'skale-api sla bounty skale-admin'
COMPOSE_TIMEOUT = 10


def remove_compose_containers(env):
    logger.info(f'Going to remove {MAIN_COMPOSE_CONTAINERS} containers')
    run_cmd(
        cmd=f'docker-compose -f {COMPOSE_PATH} rm -s -f {MAIN_COMPOSE_CONTAINERS}'.split(),
        env=env
    )
    logger.info(f'Going to sleep for {COMPOSE_TIMEOUT} seconds')
    sleep(COMPOSE_TIMEOUT)
    logger.info(f'Going to remove all compose containers')
    run_cmd(
        cmd=f'docker-compose -f {COMPOSE_PATH} rm -s -f'.split(),
        env=env
    )
    logger.info(f'Compose containers removed')


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


def docker_lvmpy_update():
    update_docker_lvmpy_sources()


def update_docker_lvmpy_sources():
    logger.info('Updating docker-lvmpy sources')
    # docker_lvmpy_repo = Repo(DOCKER_LVMPY_PATH)
    docker_lvmpy_remote = Remote(DOCKER_LVMPY_PATH, 'docker-lvmpy')
    docker_lvmpy_remote.fetch()


def download_skale_node_release():
    pass


def run_compose_containers():
    pass
