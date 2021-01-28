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
import docker
from time import sleep
from docker.client import DockerClient

from tools.helper import run_cmd, str_to_bool
from configs import COMPOSE_PATH, SKALE_DIR, SGX_CERTIFICATES_DIR_NAME


logger = logging.getLogger(__name__)

SCHAIN_REMOVE_TIMEOUT = 40
IMA_REMOVE_TIMEOUT = 20

MAIN_COMPOSE_CONTAINERS = 'skale-api sla bounty skale-admin'
BASE_COMPOSE_SERVICES = 'transaction-manager skale-admin skale-api mysql sla bounty nginx watchdog filebeat' # noqa
MONITORING_COMPOSE_SERVICES = 'node-exporter advisor'
NOTIFICATION_COMPOSE_SERVICES = 'celery redis'
COMPOSE_TIMEOUT = 10


def docker_client() -> DockerClient:
    return docker.from_env()


def get_all_schain_containers(_all=False) -> list:
    return docker_client().containers.list(all=_all, filters={'name': 'skale_schain_*'})


def get_all_ima_containers(all=False, format=False) -> list:
    return docker_client().containers.list(all=all, filters={'name': 'skale_ima_*'})


def rm_all_schain_containers():
    schain_containers = get_all_schain_containers()
    remove_containers(schain_containers, timeout=SCHAIN_REMOVE_TIMEOUT)


def rm_all_ima_containers():
    ima_containers = get_all_ima_containers()
    remove_containers(ima_containers, timeout=IMA_REMOVE_TIMEOUT)


def remove_containers(containers, timeout):
    for container in containers:
        logger.info(f'Removing container: {container.name}')
        safe_remove_container(container, timeout=timeout)


def safe_remove_container(container, timeout=10):
    container.stop(timeout=timeout)
    container.remove()


def compose_rm(env):
    logger.info(f'Removing {MAIN_COMPOSE_CONTAINERS} containers')
    run_cmd(
        cmd=f'docker-compose -f {COMPOSE_PATH} rm -s -f {MAIN_COMPOSE_CONTAINERS}'.split(),
        env=env
    )
    logger.info(f'Sleeping for {COMPOSE_TIMEOUT} seconds')
    sleep(COMPOSE_TIMEOUT)
    logger.info(f'Removing all compose containers')
    run_cmd(
        cmd=f'docker-compose -f {COMPOSE_PATH} rm -s -f'.split(),
        env=env
    )
    logger.info(f'Compose containers removed')


def compose_pull():
    logger.info(f'Pulling compose containers')
    run_cmd(
        cmd=f'docker-compose -f {COMPOSE_PATH} pull'.split(),
        env={
            'SKALE_DIR': SKALE_DIR
        }
    )


def compose_build():
    logger.info(f'Building compose containers')
    run_cmd(
        cmd=f'docker-compose -f {COMPOSE_PATH} build'.split(),
        env={
            'SKALE_DIR': SKALE_DIR
        }
    )


def compose_up(env):
    logger.info('Running base set of containers')

    if 'SGX_CERTIFICATES_DIR_NAME' not in env:
        env['SGX_CERTIFICATES_DIR_NAME'] = SGX_CERTIFICATES_DIR_NAME

    run_cmd(
        cmd=f'docker-compose -f {COMPOSE_PATH} up -d {BASE_COMPOSE_SERVICES}'.split(),
        env=env
    )
    if str_to_bool(env.get('MONITORING_CONTAINERS', '')):
        logger.info('Running monitoring containers')
        run_cmd(
            cmd=f'docker-compose -f {COMPOSE_PATH} up -d {MONITORING_COMPOSE_SERVICES}'.split(),
            env=env
        )
    if 'TG_API_KEY' in env and 'TG_CHAT_ID' in env:
        logger.info('Running containers for Telegram notifications')
        run_cmd(
            cmd=f'docker-compose -f {COMPOSE_PATH} up -d {NOTIFICATION_COMPOSE_SERVICES}'.split(),
            env=env
        )
