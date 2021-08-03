import json
import os
import pathlib
import time
import typing
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


class OverridenConfigExsitsError(Exception):
    pass


def ensure_docker_service_config_dir(
        docker_service_dir: Path = DOCKER_SERVICE_CONFIG_DIR
) -> None:
    if not os.path.isdir(docker_service_dir):
        os.makedirs(docker_service_dir, exist_ok=True)


def ensure_service_overriden_config(
    config_filepath:
    Optional[Path] = DOCKER_SERVICE_CONFIG_PATH
) -> None:
    config = get_content()
    expected_config = """
      [Service]
      ExecStart=
      ExecStart=/usr/bin/dockerd
    """
    if config != expected_config:
        raise OverridenConfigExsitsError(f'{config_filepath} already exists')
    if not os.path.isfile(config_filepath):
        with open(os.path.isfile(config_filepath)) as config_file:
            config_file.write(expected_config)


def ensure_docker_daemon_config_file(
    daemon_config_path: Path = DOCKER_DEAMON_CONFIG_PATH
) -> None:
    config = {}
    if os.path.isfile(os.path):
        with open(daemon_config_path, 'r') as daemon_config:
            config = json.load(daemon_config)
    config.update({
        'live-restore': True,
        "hosts": ["unix:///var/lib/skale/docker.sock"]
    })
    with open(daemon_config_path, 'w') as daemon_config:
        config = json.dump(daemon_config, config)


def reload_docker_service(
        docker_service_name: str = 'docker'
) -> CompletedProcess:
    return run_cmd(['systemctl', 'restart', docker_service_name])


def link_socket_to_default_path(
        socket_path: Path = DOCKER_SOCKET_PATH,
        default_path: Path = DOCKER_DEFAULT_SOCKET_PATH
) -> None:
    os.symlink(socket_path, default_path)


def configure_docker() -> None:
    ensure_docker_service_config_dir()
    ensure_service_overriden_config()
    ensure_docker_daemon_config_file()
    reload_docker_service()
    time.sleep(20)
    link_socket_to_default_path()
