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
from time import sleep

import docker
from docker.client import DockerClient
from docker.models.containers import Container

from tools.helper import run_cmd, str_to_bool
from configs import (COMPOSE_PATH, SKALE_DIR, SGX_CERTIFICATES_DIR_NAME,
                     REMOVED_CONTAINERS_FOLDER_PATH)


logger = logging.getLogger(__name__)

SCHAIN_REMOVE_TIMEOUT = 40
IMA_REMOVE_TIMEOUT = 20

MAIN_COMPOSE_CONTAINERS = 'skale-api sla bounty skale-admin'
BASE_COMPOSE_SERVICES = 'transaction-manager skale-admin skale-api mysql sla bounty nginx watchdog filebeat' # noqa
MONITORING_COMPOSE_SERVICES = 'node-exporter advisor'
NOTIFICATION_COMPOSE_SERVICES = 'celery redis'
COMPOSE_TIMEOUT = 10

DOCKER_DEFAULT_STOP_TIMEOUT = 20
DOCKER_DEFAULT_TAIL_LINES = 10000


def docker_client() -> DockerClient:
    return docker.from_env()


def get_all_schain_containers(_all=True) -> list:
    return docker_client().containers.list(all=_all, filters={'name': 'skale_schain_*'})


def get_all_ima_containers(_all=True) -> list:
    return docker_client().containers.list(all=_all, filters={'name': 'skale_ima_*'})


def rm_all_schain_containers():
    schain_containers = get_all_schain_containers()
    remove_containers(schain_containers, stop_timeout=SCHAIN_REMOVE_TIMEOUT)


def rm_all_ima_containers():
    ima_containers = get_all_ima_containers()
    remove_containers(ima_containers, stop_timeout=IMA_REMOVE_TIMEOUT)


def remove_containers(containers, stop_timeout):
    for container in containers:
        logger.info(f'Removing container: {container.name}')
        safe_rm(container, stop_timeout=stop_timeout)


def safe_rm(container: Container, stop_timeout=DOCKER_DEFAULT_STOP_TIMEOUT, **kwargs):
    """
    Saves docker container logs (last N lines) in the .skale/node_data/log/.removed_containers
    folder. Then stops and removes container with specified params.
    """
    container_name = container.name
    backup_container_logs(container)
    logger.debug(f'Stopping container: {container_name}, timeout: {stop_timeout}')
    container.stop(timeout=stop_timeout)
    logger.debug(f'Removing container: {container_name}, kwargs: {kwargs}')
    container.remove(**kwargs)
    logger.info(f'Container removed: {container_name}')


def backup_container_logs(container: Container, tail=DOCKER_DEFAULT_TAIL_LINES) -> None:
    logger.info(f'Going to backup container logs: {container.name}')
    logs_backup_filepath = get_logs_backup_filepath(container)
    with open(logs_backup_filepath, "wb") as out:
        out.write(container.logs(tail=tail))
    logger.debug(f'Old container logs saved to {logs_backup_filepath}, tail: {tail}')


def get_logs_backup_filepath(container: Container) -> str:
    container_index = sum(1 for f in os.listdir(REMOVED_CONTAINERS_FOLDER_PATH)
                          if f.startswith(f'{container.name}-'))
    log_file_name = f'{container.name}-{container_index}.log'
    return os.path.join(REMOVED_CONTAINERS_FOLDER_PATH, log_file_name)


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
