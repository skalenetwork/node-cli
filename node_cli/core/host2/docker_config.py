import json
import os
from pathlib import Path
from typing import Optional

from node_cli.configs import DOCKER_SERVICE_CONFIG_DIR


def get_content(filename: Path) -> Optional[str]:
    if not os.path.isfile(filename):
        return None
    with open(filename) as f:
        return f.read()


class DockerConfigError(Exception):
    pass


class OverridenConfigExsitsError(Exception):
    pass


def ensure_docker_service_config_dir():
    if not os.path.isdir(DOCKER_SERVICE_CONFIG_DIR):
        os.makedirs(DOCKER_SERVICE_CONFIG_DIR, exist_ok=True)


def ensure_service_overriden_config(
    config_filepath:
    Optional[Path] = None
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
    daemon_config_path: Optional[Path] = None
):
    config = {}
    if os.path.isfile(os.path):
        with open(daemon_config_path, 'r') as daemon_config:
            config = json.load(daemon_config)
    config.update({
        'live-restore': True,
        "hosts": ["unix:///var/lib/skale/docker.sock"]
    })
    with open(daemon_config_path, 'w') as daemon_config:
        config = json.write(daemon_config, config)
