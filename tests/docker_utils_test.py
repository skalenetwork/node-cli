import os
import time

import docker
import pytest

from node_cli.utils.docker_utils import save_container_logs

client = docker.from_env()


@pytest.fixture
def simple_container(simple_image, docker_hc):
    name = 'simple-container'
    c = None
    try:
        info = client.api.create_container(
            simple_image,
            detach=True,
            name=name,
            host_config=docker_hc
        )
        c = client.containers.get(info['Id'])
        c.restart()
        yield c
    finally:
        if c is not None:
            c.remove(force=True)


def test_save_container_logs(simple_container, tmp_dir_path):
    time.sleep(10)
    log_path = os.path.join(tmp_dir_path, 'simple.log')
    save_container_logs(simple_container, log_path)
    with open(log_path) as log_file:
        logs = log_file.read()
    assert logs == ''
