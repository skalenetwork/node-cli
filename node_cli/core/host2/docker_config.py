import enum
import filecmp
import json
import logging
import os
import pathlib
import time
import typing
from typing import Optional

from node_cli.configs import (
    DOCKER_DEAMON_CONFIG_PATH,
    DOCKER_DEFAULT_SOCKET_PATH,
    DOCKER_SERVICE_CONFIG_DIR,
    DOCKER_SERVICE_CONFIG_PATH,
    DOCKER_SOCKET_PATH
)
from node_cli.utils.helper import run_cmd

logger = logging.getLogger(__name__)


Path = typing.Union[str, pathlib.Path]


def get_content(filename: Path) -> Optional[str]:
    if not os.path.isfile(filename):
        return None
    with open(filename) as f:
        return f.read()


class DockerConfigError(Exception):
    pass


class OverridenConfigExsitsError(DockerConfigError):
    pass


class NoSocketFileError(DockerConfigError):
    pass


class DockerConfigResult(enum.IntEnum):
    UNCHANGED = 0
    CHANGED = 1


def ensure_docker_service_config_dir(
        docker_service_dir: Path = DOCKER_SERVICE_CONFIG_DIR
) -> DockerConfigResult:
    logger.info('Ensuring docker service dir')
    if not os.path.isdir(docker_service_dir):
        logger.info('Creating docker service dir')
        os.makedirs(docker_service_dir, exist_ok=True)
        return DockerConfigResult.CHANGED
    return DockerConfigResult.UNCHANGED


def ensure_service_overriden_config(
    config_filepath:
    Optional[Path] = DOCKER_SERVICE_CONFIG_PATH
) -> DockerConfigResult:
    logger.info('Ensuring docker service override config')
    config = get_content(config_filepath)
    expected_config = '\n'.join(
        ['[Service]', 'ExecStart=', 'ExecStart=/usr/bin/dockerd']
    )

    if not os.path.isfile(config_filepath):
        with open(config_filepath, 'w') as config_file:
            logger.info('Creating docker service override config')
            config_file.write(expected_config)
            return DockerConfigResult.CHANGED
    elif config != expected_config:
        raise OverridenConfigExsitsError(
            f'{config_filepath} already exists'
        )
    return DockerConfigResult.UNCHANGED


def ensure_docker_daemon_config(
    daemon_config_path: Path = DOCKER_DEAMON_CONFIG_PATH
) -> None:
    logger.info('Ensuring docker daemon config')
    config = {}
    if os.path.isfile(daemon_config_path):
        with open(daemon_config_path, 'r') as daemon_config:
            config = json.load(daemon_config)
    if config.get('live-restore') is True and \
       config.get('hosts') == ['unix:///var/lib/skale/docker.sock']:
        return DockerConfigResult.UNCHANGED
    config.update({
        'live-restore': True,
        'hosts': ['unix:///var/lib/skale/docker.sock']
    })
    logger.info('Updating docker daemon config')
    with open(daemon_config_path, 'w') as daemon_config:
        config = json.dump(config, daemon_config)
    return DockerConfigResult.CHANGED


def restart_docker_service(
        docker_service_name: str = 'docker'
) -> DockerConfigResult:
    logger.info('Restarting docker service')
    run_cmd(['systemctl', 'restart', docker_service_name])
    return DockerConfigResult.CHANGED


def link_socket_to_default_path(
        socket_path: Path = DOCKER_SOCKET_PATH,
        default_path: Path = DOCKER_DEFAULT_SOCKET_PATH
) -> None:
    logger.info('Ensuring symlink to custom docker socket')
    if not os.path.isfile(socket_path):
        raise NoSocketFileError(f'socket {socket_path} does not exist')
    if os.path.islink(default_path) and \
       filecmp.cmp(socket_path, default_path):
        return DockerConfigResult.UNCHANGED
    logger.info('Creating symlink to custom docker socket')
    os.symlink(socket_path, default_path)
    return DockerConfigResult.CHANGED


def configure_docker() -> None:
    logger.info('Configuring docker')
    pre_restart_tasks = [
        ensure_docker_service_config_dir,
        ensure_service_overriden_config,
        ensure_docker_daemon_config
    ]
    results = [
        task()
        for task in pre_restart_tasks
    ]
    if any(results, DockerConfigResult.CHANGED):
        restart_docker_service()
        time.sleep(20)
    link_socket_to_default_path()
    logger.info('Docker configuration finished')
