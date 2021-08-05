import enum
import json
import logging
import os
import pathlib
import time
import typing
from typing import Optional, Tuple


from node_cli.configs import (
    DOCKER_DEAMON_CONFIG_PATH,
    DOCKER_DAEMON_HOSTS,
    DOCKER_SERVICE_CONFIG_DIR,
    DOCKER_SERVICE_CONFIG_PATH,
    DOCKER_SOCKET_PATH,
    SKALE_RUN_DIR
)
from node_cli.utils.helper import run_cmd
from node_cli.utils.docker_utils import docker_client, get_containers


logger = logging.getLogger(__name__)


Path = typing.Union[str, pathlib.Path]


def get_content(filename: Path) -> Optional[str]:
    if not os.path.isfile(filename):
        return None
    with open(filename) as f:
        return f.read()


gdclient = docker_client()


class DockerConfigError(Exception):
    pass


class OverridenConfigExsitsError(DockerConfigError):
    pass


class NoSocketFileError(DockerConfigError):
    pass


class ContainersExistError(DockerConfigError):
    pass


class SocketInitTimeoutError(DockerConfigError):
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
        daemon_config_path: Path = DOCKER_DEAMON_CONFIG_PATH,
        daemon_hosts: Path = DOCKER_DAEMON_HOSTS
) -> None:
    logger.info('Ensuring docker daemon config')
    config = {}
    if os.path.isfile(daemon_config_path):
        with open(daemon_config_path, 'r') as daemon_config:
            config = json.load(daemon_config)
    if config.get('live-restore') is True and \
       config.get('hosts') == daemon_hosts:
        return DockerConfigResult.UNCHANGED
    config.update({
        'live-restore': True,
        'hosts': daemon_hosts
    })
    logger.info('Updating docker daemon config')
    with open(daemon_config_path, 'w') as daemon_config:
        config = json.dump(config, daemon_config)
    return DockerConfigResult.CHANGED


def restart_docker_service(
        docker_service_name: str = 'docker'
) -> DockerConfigResult:
    logger.info('Executing daemon-reload')
    run_cmd(['systemctl', 'daemon-reload'])

    logger.info('Restarting docker service')
    run_cmd(['systemctl', 'restart', docker_service_name])
    return DockerConfigResult.CHANGED


def is_socket_existed(socket_path: Path = DOCKER_SOCKET_PATH) -> bool:
    return os.path.exists(socket_path)


def wait_for_socket_initialization(
        socket_path: Path = DOCKER_SOCKET_PATH,
        allowed_time: int = 300
) -> None:
    logger.info('Waiting for docker inititalization')
    start_ts = time.time()
    while int(time.time() - start_ts) < allowed_time and \
            not is_socket_existed():
        time.sleep(2)
    if not is_socket_existed():
        raise SocketInitTimeoutError(
            f'Socket was not able to init in {allowed_time}'
        )
    logger.info('Socket initialized successfully')


def ensure_run_dir(run_dir: Path = SKALE_RUN_DIR) -> DockerConfigResult:
    if not os.path.isdir(run_dir):
        os.makedirs(run_dir)
        return DockerConfigResult.CHANGED
    return DockerConfigResult.UNCHANGED


def assert_no_containers(ignore: Tuple[str] = ()):
    containers = [
        c.name
        for c in get_containers()
        if c.name not in ignore
    ]
    if len(containers) > 0:
        logger.fatal('%s containers exist', ' '.join(containers))
        raise ContainersExistError(
            f'Existed containers amount {len(containers)}'
        )


def configure_docker() -> None:
    logger.info('Checking that there are no containers')
    assert_no_containers()
    logger.info('Configuring docker')
    pre_restart_tasks = (
        ensure_run_dir,
        ensure_docker_service_config_dir,
        ensure_service_overriden_config,
        ensure_docker_daemon_config
    )
    results = (task() for task in pre_restart_tasks)
    results = list(results)
    logger.info('Docker config changes %s', results)
    if not is_socket_existed() or \
       any(r == DockerConfigResult.CHANGED for r in results):
        restart_docker_service()
        wait_for_socket_initialization()

    logger.info('Docker configuration finished')
