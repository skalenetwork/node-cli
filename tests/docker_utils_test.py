import os
import time
from time import sleep

import pytest

from node_cli.utils.docker_utils import (
    docker_cleanup,
    save_container_logs,
    safe_rm
)
from node_cli.configs import REMOVED_CONTAINERS_FOLDER_PATH


@pytest.fixture
def simple_container(dclient, simple_image, docker_hc):
    name = 'simple-container'
    c = None
    try:
        info = dclient.api.create_container(
            simple_image,
            detach=True,
            name=name,
            host_config=docker_hc
        )
        c = dclient.containers.get(info['Id'])
        c.restart()
        yield c
    finally:
        if c is not None:
            try:
                c.remove(force=True)
            except Exception:
                pass


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
        '================================================================================\n',
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


def test_safe_rm(simple_container, removed_containers_folder):
    sleep(10)
    safe_rm(simple_container)
    log_path = os.path.join(REMOVED_CONTAINERS_FOLDER_PATH, 'simple-container-0.log')
    with open(log_path) as log_file:
        log_lines = log_file.readlines()
    assert log_lines[-1] == 'signal_handler completed, exiting...\n'


def test_docker_cleanup(dclient, simple_container):
    c = simple_container
    image = c.image
    docker_cleanup(dclient=dclient)
    assert image in dclient.images.list()

    c.stop()
    docker_cleanup(dclient=dclient)
    assert image in dclient.images.list()

    c.remove()
    docker_cleanup(dclient=dclient)
    assert image not in dclient.images.list()
