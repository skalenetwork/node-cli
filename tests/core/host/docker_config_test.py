import os

import pytest

from node_cli.core.host2.docker_config import ensure_docker_service_config_dir


def test_ensure_docker_service_config_dir(tmp_dir) -> None:
    service_config_dir = os.path.join(tmp_dir, 'docker.service.d')
    ensure_docker_service_config_dir(
        service_config_dir,
        service_config_dir
    )
    assert os.path.isdir(service_config_dir)
