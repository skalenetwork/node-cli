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

from tools.docker_utils import rm_all_schain_containers, rm_all_ima_containers
from configs import COMPOSE_PATH
from tools.helper import run_cmd

logger = logging.getLogger(__name__)


MAIN_COMPOSE_CONTAINERS = 'skale-api sla bounty skale-admin'
COMPOSE_TIMEOUT = 10


def update_procedure(env):
    remove_compose_containers(env)
    remove_dynamic_containers(env)

    backup_old_contracts()
    download_contracts()
    docker_lvmpy_update()

    download_skale_node_release()
    run_compose_containers()


def remove_compose_containers(env):
    logger.info(f'Going to remove {MAIN_COMPOSE_CONTAINERS} containers, \
                compose file: {COMPOSE_PATH}')
    run_cmd(
        cmd=f'docker-compose -f {COMPOSE_PATH} rm -s -f {MAIN_COMPOSE_CONTAINERS}'.split(),
        env=env
    )
    logger.info(f'Going to sleep for {COMPOSE_TIMEOUT} seconds')
    sleep(COMPOSE_TIMEOUT)
    logger.info(f'Going to remove all compose containers, \
                compose file: {COMPOSE_PATH}')
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
    pass


def download_contracts():
    pass


def docker_lvmpy_update():
    pass


def download_skale_node_release():
    pass


def run_compose_containers():
    pass
