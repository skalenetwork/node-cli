import json
import os
import pathlib
import time
import typing
from collections import namedtuple
from subprocess import CompletedProcess
from typing import Optional

from node_cli.configs import (
    DOCKER_DEAMON_CONFIG_PATH,
    DOCKER_DEFAULT_SOCKET_PATH,
    DOCKER_SERVICE_CONFIG_DIR,
    DOCKER_SERVICE_CONFIG_PATH,
    DOCKER_SOCKET_PATH
)
from node_cli.utils.helper import run_cmd

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


DockerConfigResult = namedtuple(
    'DockerConfigResult',
    'status',
    'data'
)


def ensure_docker_service_config_dir(
        docker_service_dir: Path = DOCKER_SERVICE_CONFIG_DIR
) -> None:
    if not os.path.isdir(docker_service_dir):
        os.makedirs(docker_service_dir, exist_ok=True)


def ensure_service_overriden_config(
    config_filepath:
    Optional[Path] = DOCKER_SERVICE_CONFIG_PATH
) -> None:
    config = get_content(config_filepath)
    expected_config = '\n'.join(
        ['[Service]', 'ExecStart=', 'ExecStart=/usr/bin/dockerd']
    )

    if not os.path.isfile(config_filepath):
        with open(config_filepath, 'w') as config_file:
            config_file.write(expected_config)
    elif config != expected_config:
        raise OverridenConfigExsitsError(
            f'{config_filepath} already exists'
        )


def ensure_docker_daemon_config(
    daemon_config_path: Path = DOCKER_DEAMON_CONFIG_PATH
) -> None:
    config = {}
    if os.path.isfile(daemon_config_path):
        with open(daemon_config_path, 'r') as daemon_config:
            print(daemon_config)
            config = json.load(daemon_config)
    config.update({
        'live-restore': True,
        'hosts': ['unix:///var/lib/skale/docker.sock']
    })
    with open(daemon_config_path, 'w') as daemon_config:
        config = json.dump(config, daemon_config)


def reload_docker_service(
        docker_service_name: str = 'docker'
) -> CompletedProcess:
    return run_cmd(['systemctl', 'restart', docker_service_name])


def link_socket_to_default_path(
        socket_path: Path = DOCKER_SOCKET_PATH,
        default_path: Path = DOCKER_DEFAULT_SOCKET_PATH
) -> None:
    if not os.path.isfile(socket_path):
        raise NoSocketFileError(f'socket {socket_path} does not exist')
    os.symlink(socket_path, default_path)


def configure_docker() -> None:
    ensure_docker_service_config_dir()
    ensure_service_overriden_config()
    ensure_docker_daemon_config()
    reload_docker_service()
    time.sleep(20)
    link_socket_to_default_path()
