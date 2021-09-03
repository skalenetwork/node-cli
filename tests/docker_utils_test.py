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
    time.sleep(1)
    log_path = os.path.join(tmp_dir_path, 'simple.log')
    save_container_logs(simple_container, log_path, head=5, tail=10)
    with open(log_path) as log_file:
        log_lines = log_file.readlines()
    assert log_lines == [
        'INFO:__main__:Test 0\n',
        'INFO:__main__:Test 1\n',
        'INFO:__main__:Test 2\n',
        'INFO:__main__:Test 3\n',
        'INFO:__main__:Test 4\n',
        '================================================================================\n',  # noqa
        'INFO:__main__:Test 1\n',
        'INFO:__main__:Test 2\n',
        'INFO:__main__:Test 3\n',
        'INFO:__main__:Test 4\n',
        'INFO:__main__:Test 5\n',
        'INFO:__main__:Test 6\n',
        'INFO:__main__:Test 7\n',
        'INFO:__main__:Test 8\n',
        'INFO:__main__:Test 9\n',
        'INFO:__main__:Waiting\n'
    ]
    save_container_logs(simple_container, log_path, head=10, tail=5)
    with open(log_path) as log_file:
        log_lines = log_file.readlines()
    assert log_lines == [
        'INFO:__main__:Test 0\n',
        'INFO:__main__:Test 1\n',
        'INFO:__main__:Test 2\n',
        'INFO:__main__:Test 3\n',
        'INFO:__main__:Test 4\n',
        '================================================================================\n',  # noqa
        'INFO:__main__:Test 6\n',
        'INFO:__main__:Test 7\n',
        'INFO:__main__:Test 8\n',
        'INFO:__main__:Test 9\n',
        'INFO:__main__:Waiting\n'
    ]
