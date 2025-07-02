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

import io
import itertools
import logging
import os
import time
from typing import Optional

import docker
from docker.client import DockerClient
from docker.errors import NotFound
from docker.models.containers import Container

from node_cli.configs import (
    COMPOSE_PATH,
    MIRAGE_COMPOSE_PATH,
    NGINX_CONTAINER_NAME,
    REMOVED_CONTAINERS_FOLDER_PATH,
    SGX_CERTIFICATES_DIR_NAME,
    SYNC_COMPOSE_PATH,
)
from node_cli.utils.helper import run_cmd, str_to_bool
from node_cli.utils.node_type import NodeType

logger = logging.getLogger(__name__)

SCHAIN_REMOVE_TIMEOUT = 300
IMA_REMOVE_TIMEOUT = 20
TELEGRAF_REMOVE_TIMEOUT = 20
REDIS_START_TIMEOUT = 10

REDIS_SERVICE_DICT = {'redis': 'skale_redis'}

CORE_COMMON_COMPOSE_SERVICES = {
    'transaction-manager': 'skale_transaction-manager',
    'redis': 'skale_redis',
    'watchdog': 'skale_watchdog',
    'nginx': 'skale_nginx',
    'filebeat': 'skale_filebeat',
}

BASE_SKALE_COMPOSE_SERVICES = {
    **CORE_COMMON_COMPOSE_SERVICES,
    'skale-admin': 'skale_admin',
    'skale-api': 'skale_api',
    'bounty': 'skale_bounty',
}

BASE_MIRAGE_COMPOSE_SERVICES = {
    **CORE_COMMON_COMPOSE_SERVICES,
    'mirage-admin': 'mirage_admin',
    'mirage-api': 'mirage_api',
}

BASE_MIRAGE_BOOT_COMPOSE_SERVICES = {
    **CORE_COMMON_COMPOSE_SERVICES,
    'mirage-boot': 'mirage_boot_admin',
    'mirage-boot-api': 'mirage_boot_api',
}

BASE_SYNC_COMPOSE_SERVICES = {
    'skale-sync-admin': 'skale_sync_admin',
    'nginx': 'skale_nginx',
}

MONITORING_COMPOSE_SERVICES = {
    'node-exporter': 'monitor_node_exporter',
    'advisor': 'monitor_cadvisor',
}
TELEGRAF_SERVICES = ('telegraf',)
NOTIFICATION_COMPOSE_SERVICES = ('celery',)
COMPOSE_TIMEOUT = 10

DOCKER_DEFAULT_STOP_TIMEOUT = 20

DOCKER_DEFAULT_HEAD_LINES = 400
DOCKER_DEFAULT_TAIL_LINES = 10000

COMPOSE_SHUTDOWN_TIMEOUT = 40


def docker_client() -> DockerClient:
    return docker.from_env()


def get_sanitized_container_name(container_info: dict) -> str:
    return container_info['Names'][0].replace('/', '', 1)


def get_containers(container_name_filter=None, _all=True) -> list:
    return docker_client().containers.list(all=_all)


def get_all_schain_containers(_all=True) -> list:
    return docker_client().containers.list(all=_all, filters={'name': 'skale_schain_*'})


def get_all_ima_containers(_all=True) -> list:
    return docker_client().containers.list(all=_all, filters={'name': 'skale_ima_*'})


def remove_dynamic_containers() -> None:
    logger.info('Removing sChains containers')
    rm_all_schain_containers()
    logger.info('Removing IMA containers')
    rm_all_ima_containers()
    logger.info('Removing telegraf (if exists)')
    remove_telegraf()


def rm_all_schain_containers():
    schain_containers = get_all_schain_containers()
    remove_containers(schain_containers, timeout=SCHAIN_REMOVE_TIMEOUT)


def rm_all_ima_containers():
    ima_containers = get_all_ima_containers()
    remove_containers(ima_containers, timeout=IMA_REMOVE_TIMEOUT)


def remove_telegraf() -> None:
    telegraf = docker_client().containers.list(filters={'name': 'skale_telegraf'})
    remove_containers(telegraf, timeout=TELEGRAF_REMOVE_TIMEOUT)


def remove_containers(containers, timeout):
    for container in containers:
        safe_rm(container, timeout=timeout)


def safe_rm(container: Container, timeout=DOCKER_DEFAULT_STOP_TIMEOUT, **kwargs):
    """
    Saves docker container logs (last N lines) in the .skale/node_data/log/.removed_containers
    folder. Then stops and removes container with specified params.
    """
    container_name = container.name
    logger.info(f'Stopping container: {container_name}, timeout: {timeout}')
    container.stop(timeout=timeout)
    backup_container_logs(container)
    logger.info(f'Removing container: {container_name}, kwargs: {kwargs}')
    container.remove(**kwargs)
    logger.info(f'Container removed: {container_name}')


def stop_container(
    container_name: str,
    timeout: int = DOCKER_DEFAULT_STOP_TIMEOUT,
    dclient: Optional[DockerClient] = None,
) -> None:
    dc = dclient or docker_client()
    container = dc.containers.get(container_name)
    logger.info('Stopping container: %s, timeout: %s', container_name, timeout)
    container.stop(timeout=timeout)


def rm_container(
    container_name: str,
    timeout: int = DOCKER_DEFAULT_STOP_TIMEOUT,
    dclient: Optional[DockerClient] = None,
) -> None:
    dc = dclient or docker_client()
    container_names = [container.name for container in get_containers()]
    if container_name in container_names:
        container = dc.containers.get(container_name)
        safe_rm(container)


def start_container(container_name: str, dclient: Optional[DockerClient] = None) -> None:
    dc = dclient or docker_client()
    container = dc.containers.get(container_name)
    logger.info('Starting container %s', container_name)
    container.start()


def remove_schain_container(schain_name: str, dclient: Optional[DockerClient] = None) -> None:
    container_name = f'skale_schain_{schain_name}'
    rm_container(container_name, timeout=SCHAIN_REMOVE_TIMEOUT, dclient=dclient)


def backup_container_logs(
    container: Container,
    head: int = DOCKER_DEFAULT_HEAD_LINES,
    tail: int = DOCKER_DEFAULT_TAIL_LINES,
) -> None:
    logger.info(f'Going to backup container logs: {container.name}')
    logs_backup_filepath = get_logs_backup_filepath(container)
    save_container_logs(container, logs_backup_filepath, tail)
    logger.info(f'Old container logs saved to {logs_backup_filepath}, tail: {tail}')


def save_container_logs(
    container: Container,
    log_filepath: str,
    head: int = DOCKER_DEFAULT_HEAD_LINES,
    tail: int = DOCKER_DEFAULT_TAIL_LINES,
) -> None:
    separator = b'=' * 80 + b'\n'
    tail_lines = container.logs(tail=tail)
    lines_number = len(io.BytesIO(tail_lines).readlines())
    head = min(lines_number, head)
    log_stream = container.logs(stream=True, follow=True)
    head_lines = b''.join(itertools.islice(log_stream, head))
    with open(log_filepath, 'wb') as out:
        out.write(head_lines)
        out.write(separator)
        out.write(tail_lines)


def get_logs_backup_filepath(container: Container) -> str:
    container_index = sum(
        1 for f in os.listdir(REMOVED_CONTAINERS_FOLDER_PATH) if f.startswith(f'{container.name}-')
    )
    log_file_name = f'{container.name}-{container_index}.log'
    return os.path.join(REMOVED_CONTAINERS_FOLDER_PATH, log_file_name)


def ensure_volume(name: str, size: int, driver='lvmpy', dutils=None):
    dutils = dutils or docker_client()
    if is_volume_exists(name, dutils=dutils):
        logger.info('Volume %s already exist', name)
        return
    logger.info('Creating volume %s, size: %d', name, size)
    driver_opts = {'size': str(size)} if driver == 'lvmpy' else None
    volume = dutils.volumes.create(name=name, driver=driver, driver_opts=driver_opts)
    return volume


def is_volume_exists(name: str, dutils=None):
    dutils = dutils or docker_client()
    try:
        dutils.volumes.get(name)
    except NotFound:
        return False
    return True


def compose_rm(node_type: NodeType, env={}):
    logger.info('Removing compose containers')
    compose_path = get_compose_path(node_type)
    run_cmd(
        cmd=(
            'docker',
            'compose',
            '-f',
            compose_path,
            'down',
            '-t',
            str(COMPOSE_SHUTDOWN_TIMEOUT),
        ),
        env=env,
    )
    logger.info('Compose containers removed')


def compose_pull(env: dict, node_type: NodeType):
    logger.info('Pulling compose containers')
    compose_path = get_compose_path(node_type)
    run_cmd(cmd=('docker', 'compose', '-f', compose_path, 'pull'), env=env)


def compose_build(env: dict, node_type: NodeType):
    logger.info('Building compose containers')
    compose_path = get_compose_path(node_type)
    run_cmd(cmd=('docker', 'compose', '-f', compose_path, 'build'), env=env)


def get_compose_path(node_type: NodeType) -> str:
    if node_type == NodeType.SYNC:
        return SYNC_COMPOSE_PATH
    elif node_type == NodeType.MIRAGE:
        return MIRAGE_COMPOSE_PATH
    else:
        return COMPOSE_PATH


def get_compose_services(node_type: NodeType) -> list[str]:
    if node_type == NodeType.SYNC:
        result = list(BASE_SYNC_COMPOSE_SERVICES)
    elif node_type == NodeType.MIRAGE:
        result = list(BASE_MIRAGE_COMPOSE_SERVICES)
    else:
        result = list(BASE_SKALE_COMPOSE_SERVICES)

    return result


def get_up_compose_cmd(node_type: NodeType, services: list[str] | None = None) -> tuple:
    compose_path = get_compose_path(node_type)

    if services is None:
        services = get_compose_services(node_type)

    return ('docker', 'compose', '-f', compose_path, 'up', '-d', *services)


def compose_up(
    env, node_type: NodeType, is_mirage_boot: bool = False, services: list[str] | None = None
):
    if node_type == NodeType.SYNC:
        logger.info('Running containers for sync node')
        run_cmd(cmd=get_up_compose_cmd(node_type=NodeType.SYNC), env=env)
        return

    if 'SGX_CERTIFICATES_DIR_NAME' not in env:
        env['SGX_CERTIFICATES_DIR_NAME'] = SGX_CERTIFICATES_DIR_NAME

    if node_type == NodeType.MIRAGE:
        logger.info('Running mirage base set of containers')
        if is_mirage_boot:
            logger.debug('Launching mirage boot containers with env %s', env)
            run_cmd(
                cmd=get_up_compose_cmd(
                    node_type=NodeType.MIRAGE, services=list(BASE_MIRAGE_BOOT_COMPOSE_SERVICES)
                ),
                env=env,
            )
        else:
            logger.debug('Launching mirage containers with env %s', env)
            run_cmd(cmd=get_up_compose_cmd(node_type=NodeType.MIRAGE, services=services), env=env)
    else:
        logger.info('Running skale node base set of containers')
        logger.debug('Launching skale node containers with env %s', env)
        run_cmd(cmd=get_up_compose_cmd(node_type=NodeType.REGULAR), env=env)

        if 'TG_API_KEY' in env and 'TG_CHAT_ID' in env:
            logger.info('Running containers for Telegram notifications')
            run_cmd(
                cmd=get_up_compose_cmd(
                    node_type=NodeType.REGULAR, services=list(NOTIFICATION_COMPOSE_SERVICES)
                ),
                env=env,
            )

    if str_to_bool(env.get('MONITORING_CONTAINERS', 'False')):
        logger.info('Running monitoring containers')
        run_cmd(
            cmd=get_up_compose_cmd(
                node_type=NodeType.REGULAR, services=list(MONITORING_COMPOSE_SERVICES)
            ),
            env=env,
        )


def restart_nginx_container(dutils=None):
    dutils = dutils or docker_client()
    nginx_container = dutils.containers.get(NGINX_CONTAINER_NAME)
    nginx_container.restart()


def remove_images(images, dclient=None):
    dc = dclient or docker_client()
    for image in images:
        dc.images.remove(image.id)


def get_used_images(dclient=None):
    dc = dclient or docker_client()
    return [c.image for c in dc.containers.list()]


def cleanup_unused_images(dclient=None, ignore=None):
    logger.info('Removing unused docker images')
    ignore = ignore or []
    dc = dclient or docker_client()
    used = get_used_images(dclient=dc)
    remove_images(filter(lambda i: i not in used and i not in ignore, dc.images.list()), dclient=dc)


def is_container_running(name: str, dclient: Optional[DockerClient] = None) -> bool:
    dc = dclient or docker_client()
    try:
        container = dc.containers.get(name)
        return container.status == 'running'
    except NotFound:
        return False


def is_api_running(node_type: NodeType, dclient: Optional[DockerClient] = None) -> bool:
    if node_type == NodeType.MIRAGE:
        return is_container_running(name='mirage_api', dclient=dclient)
    else:
        return is_container_running(name='skale_api', dclient=dclient)


def is_admin_running(node_type: NodeType, client: Optional[DockerClient] = None) -> bool:
    if node_type == NodeType.MIRAGE:
        result = is_container_running(name='mirage_admin', dclient=client)
    elif node_type == NodeType.SYNC:
        result = is_container_running(name='skale_sync_admin', dclient=client)
    else:
        result = is_container_running(name='skale_admin', dclient=client)

    return result


def system_prune():
    logger.info('Removing dangling docker artifacts')
    cmd = ['docker', 'system', 'prune', '-f']
    run_cmd(cmd=cmd)


def docker_cleanup(dclient=None, ignore=None):
    ignore = ignore or []
    try:
        dc = dclient or docker_client()
        cleanup_unused_images(dclient=dc, ignore=ignore)
        system_prune()
    except Exception as e:
        logger.warning('Image cleanup errored with %s', e)


def wait_for_container(container_name: str, attempts: int = 10, interval: int = 3) -> bool:
    logger.info('Waiting for container %s to be up', container_name)
    dc = docker_client()

    for i in range(attempts):
        try:
            container = dc.containers.get(container_name)
            if container.status == 'running':
                logger.info('Container %s is up', container_name)
                return True
        except NotFound:
            logger.warning('Container %s not found, retrying...', container_name)
        time.sleep(interval)
    return False
