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
    FAIR_COMPOSE_PATH,
    NGINX_CONTAINER_NAME,
    REMOVED_CONTAINERS_FOLDER_PATH,
    SGX_CERTIFICATES_DIR_NAME,
)
from node_cli.core.node_options import active_fair, active_skale, passive_fair, passive_skale
from node_cli.utils.helper import run_cmd, str_to_bool
from node_cli.utils.node_type import NodeMode, NodeType

logger = logging.getLogger(__name__)

SCHAIN_REMOVE_TIMEOUT = 300
IMA_REMOVE_TIMEOUT = 20
TELEGRAF_REMOVE_TIMEOUT = 20
REDIS_START_TIMEOUT = 10

REDIS_SERVICE_DICT = {'redis': 'sk_redis'}

CORE_COMMON_COMPOSE_SERVICES = {
    'transaction-manager': 'sk_tm',
    'redis': 'sk_redis',
    'watchdog': 'sk_watchdog',
    'nginx': 'sk_nginx',
    'filebeat': 'sk_filebeat',
}

BASE_SKALE_COMPOSE_SERVICES = {
    **CORE_COMMON_COMPOSE_SERVICES,
    'admin': 'sk_admin',
    'api': 'sk_api',
    'bounty': 'sk_bounty',
}

BASE_FAIR_COMPOSE_SERVICES = {
    **CORE_COMMON_COMPOSE_SERVICES,
    'admin': 'sk_admin',
    'api': 'sk_api',
}

BASE_FAIR_BOOT_COMPOSE_SERVICES = {
    **CORE_COMMON_COMPOSE_SERVICES,
    'boot-admin': 'sk_boot_admin',
    'boot-api': 'sk_boot_api',
}

BASE_PASSIVE_COMPOSE_SERVICES = {
    'admin': 'sk_admin',
    'nginx': 'sk_nginx',
    'api': 'sk_api',
    'watchdog': 'sk_watchdog',
    **REDIS_SERVICE_DICT,
}

BASE_PASSIVE_FAIR_COMPOSE_SERVICES = {
    'admin': 'sk_admin',
    'api': 'sk_api',
    'nginx': 'sk_nginx',
    'watchdog': 'sk_watchdog',
    'filebeat': 'sk_filebeat',
    **REDIS_SERVICE_DICT,
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
    filters = {}
    if container_name_filter:
        filters['name'] = container_name_filter
    return docker_client().containers.list(all=_all, filters=filters)


def get_all_schain_containers(_all=True) -> list:
    return docker_client().containers.list(all=_all, filters={'name': 'sk_skaled_*'})


def get_all_ima_containers(_all=True) -> list:
    return docker_client().containers.list(all=_all, filters={'name': 'sk_ima_*'})


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


def stop_container_by_name(
    container_name: str,
    timeout: int = DOCKER_DEFAULT_STOP_TIMEOUT,
    dclient: Optional[DockerClient] = None,
) -> None:
    dc = dclient or docker_client()
    container = dc.containers.get(container_name)
    logger.info('Stopping container: %s, timeout: %s', container_name, timeout)
    container.stop(timeout=timeout)


def remove_container_by_name(
    container_name: str,
    timeout: int = DOCKER_DEFAULT_STOP_TIMEOUT,
    dclient: Optional[DockerClient] = None,
) -> None:
    dc = dclient or docker_client()
    container_names = [container.name for container in get_containers()]
    if container_name in container_names:
        container = dc.containers.get(container_name)
        safe_rm(container, timeout=timeout)


def start_container_by_name(container_name: str, dclient: Optional[DockerClient] = None) -> None:
    dc = dclient or docker_client()
    container = dc.containers.get(container_name)
    logger.info('Starting container %s', container_name)
    container.start()


def remove_schain_container_by_name(
    schain_name: str, dclient: Optional[DockerClient] = None
) -> None:
    container_name = f'sk_skaled_{schain_name}'
    remove_container_by_name(container_name, timeout=SCHAIN_REMOVE_TIMEOUT, dclient=dclient)


def backup_container_logs(
    container: Container,
    tail: int | str = DOCKER_DEFAULT_TAIL_LINES,
) -> None:
    logger.info(f'Going to backup container logs: {container.name}')
    logs_backup_filepath = get_logs_backup_filepath(container)
    save_container_logs(container, logs_backup_filepath, tail=tail)
    logger.info(f'Old container logs saved to {logs_backup_filepath}, tail: {tail}')


def save_container_logs(
    container: Container,
    log_filepath: str,
    head: int = DOCKER_DEFAULT_HEAD_LINES,
    tail: int | str = DOCKER_DEFAULT_TAIL_LINES,
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


def compose_rm(node_type: NodeType, node_mode: NodeMode, env={}):
    logger.info('Removing compose containers')
    compose_path = get_compose_path(node_type, node_mode)
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


def compose_pull(env: dict, node_type: NodeType, node_mode: NodeMode):
    logger.info('Pulling compose containers')
    compose_path = get_compose_path(node_type, node_mode)
    run_cmd(cmd=('docker', 'compose', '-f', compose_path, 'pull'), env=env)


def compose_build(env: dict, node_type: NodeType, node_mode: NodeMode):
    logger.info('Building compose containers')
    compose_path = get_compose_path(node_type, node_mode)
    run_cmd(cmd=('docker', 'compose', '-f', compose_path, 'build'), env=env)


def get_compose_path(node_type: NodeType, node_mode: NodeMode) -> str:
    if node_type == NodeType.FAIR:
        return FAIR_COMPOSE_PATH
    return COMPOSE_PATH


def get_compose_services(node_type: NodeType, node_mode: NodeMode) -> list[str]:
    if passive_skale(node_type, node_mode):
        return list(BASE_PASSIVE_COMPOSE_SERVICES)
    elif active_fair(node_type, node_mode):
        return list(BASE_FAIR_COMPOSE_SERVICES)
    elif passive_fair(node_type, node_mode):
        return list(BASE_PASSIVE_FAIR_COMPOSE_SERVICES)
    return list(BASE_SKALE_COMPOSE_SERVICES)


def get_up_compose_cmd(
    node_type: NodeType, node_mode: NodeMode, services: list[str] | None = None
) -> tuple:
    compose_path = get_compose_path(node_type, node_mode)

    if services is None:
        services = get_compose_services(node_type, node_mode)

    return ('docker', 'compose', '-f', compose_path, 'up', '-d', *services)


def compose_up(
    env,
    node_type: NodeType,
    node_mode: NodeMode,
    is_fair_boot: bool = False,
    services: list[str] | None = None,
):
    env['PASSIVE_NODE'] = str(node_mode == NodeMode.PASSIVE)
    if passive_skale(node_type, node_mode) or passive_fair(node_type, node_mode):
        logger.info('Running containers for passive node')
        run_cmd(cmd=get_up_compose_cmd(node_type=node_type, node_mode=node_mode), env=env)
        return

    if active_fair(node_type, node_mode):
        logger.info('Running fair base set of containers')
        if is_fair_boot:
            logger.debug('Launching fair boot containers with env %s', env)
            run_cmd(
                cmd=get_up_compose_cmd(
                    node_type=node_type,
                    node_mode=node_mode,
                    services=list(BASE_FAIR_BOOT_COMPOSE_SERVICES),
                ),
                env=env,
            )
        else:
            logger.debug('Launching fair containers with env %s', env)
            run_cmd(
                cmd=get_up_compose_cmd(
                    node_type=node_type,
                    node_mode=node_mode,
                    services=services,
                ),
                env=env,
            )
    elif active_skale(node_type, node_mode):
        logger.info('Running skale node base set of containers')
        logger.debug('Launching skale node containers with env %s', env)
        run_cmd(cmd=get_up_compose_cmd(node_type=node_type, node_mode=node_mode), env=env)

        if 'TG_API_KEY' in env and 'TG_CHAT_ID' in env:
            logger.info('Running containers for Telegram notifications')
            run_cmd(
                cmd=get_up_compose_cmd(
                    node_type=NodeType.SKALE,
                    node_mode=node_mode,
                    services=list(NOTIFICATION_COMPOSE_SERVICES),
                ),
                env=env,
            )

    if str_to_bool(env.get('MONITORING_CONTAINERS', 'False')):
        logger.info('Running monitoring containers')
        run_cmd(
            cmd=get_up_compose_cmd(
                node_type=NodeType.SKALE,
                node_mode=node_mode,
                services=list(MONITORING_COMPOSE_SERVICES),
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


def is_api_running(dclient: Optional[DockerClient] = None) -> bool:
    return is_container_running(name='sk_api', dclient=dclient)


def is_admin_running(dclient: Optional[DockerClient] = None) -> bool:
    return is_container_running(name='sk_admin', dclient=dclient)


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
