import time

import docker
import pytest

from node_cli.core.node import BASE_CONTAINERS_AMOUNT, is_base_containers_alive

dclient = docker.from_env()

ALPINE_IMAGE_NAME = 'alpine:3.12'
HELLO_WORLD_IMAGE_NAME = 'hello-world'
CMD = 'sleep 10'


@pytest.fixture
def skale_base_contianers():
    containers = [
        dclient.containers.run(ALPINE_IMAGE_NAME, detach=True,
                               name=f'skale_test{i}', command=CMD)
        for i in range(BASE_CONTAINERS_AMOUNT)
    ]
    yield containers
    for c in containers:
        c.remove(force=True)


@pytest.fixture
def skale_base_contianers_without_one():
    containers = [
        dclient.containers.run(ALPINE_IMAGE_NAME, detach=True,
                               name=f'skale_test{i}', command=CMD)
        for i in range(BASE_CONTAINERS_AMOUNT - 1)
    ]
    yield containers
    for c in containers:
        c.remove(force=True)


@pytest.fixture
def skale_base_contianers_exited():
    containers = [
        dclient.containers.run(HELLO_WORLD_IMAGE_NAME, detach=True,
                               name=f'skale_test{i}')
        for i in range(BASE_CONTAINERS_AMOUNT)
    ]
    time.sleep(10)
    yield containers
    for c in containers:
        c.remove(force=True)


def test_is_base_containers_alive(skale_base_contianers):
    cont = skale_base_contianers
    print([c.name for c in cont])
    assert is_base_containers_alive()


def test_is_base_containers_alive_one_failed(skale_base_contianers_without_one):
    assert not is_base_containers_alive()


def test_is_base_containers_alive_exited(skale_base_contianers_exited):
    assert not is_base_containers_alive()


def test_is_base_containers_alive_empty():
    assert not is_base_containers_alive()
