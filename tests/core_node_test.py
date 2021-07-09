import os
import shutil
import tarfile
import time
from pathlib import Path

import docker
import pytest

from node_cli.core.node import BASE_CONTAINERS_AMOUNT, is_base_containers_alive
from node_cli.core.node import pack_dir

dclient = docker.from_env()

ALPINE_IMAGE_NAME = 'alpine:3.12'
HELLO_WORLD_IMAGE_NAME = 'hello-world'
CMD = 'sleep 10'


@pytest.fixture
def skale_base_containers():
    containers = [
        dclient.containers.run(ALPINE_IMAGE_NAME, detach=True,
                               name=f'skale_test{i}', command=CMD)
        for i in range(BASE_CONTAINERS_AMOUNT)
    ]
    yield containers
    for c in containers:
        c.remove(force=True)


@pytest.fixture
def skale_base_containers_without_one():
    containers = [
        dclient.containers.run(ALPINE_IMAGE_NAME, detach=True,
                               name=f'skale_test{i}', command=CMD)
        for i in range(BASE_CONTAINERS_AMOUNT - 1)
    ]
    yield containers
    for c in containers:
        c.remove(force=True)


@pytest.fixture
def skale_base_containers_exited():
    containers = [
        dclient.containers.run(HELLO_WORLD_IMAGE_NAME, detach=True,
                               name=f'skale_test{i}')
        for i in range(BASE_CONTAINERS_AMOUNT)
    ]
    time.sleep(10)
    yield containers
    for c in containers:
        c.remove(force=True)


@pytest.fixture
def tmp_dir():
    tmp_dir = 'tmp'
    yield os.path.abspath(tmp_dir)
    shutil.rmtree(tmp_dir)


def test_pack_dir(tmp_dir):
    backup_dir = os.path.join(tmp_dir, 'backup')
    data_dir = os.path.join(backup_dir, 'data')
    trash_dir = os.path.join(backup_dir, 'trash')
    a_data = os.path.join(data_dir, 'a-data')
    b_data = os.path.join(data_dir, 'b-data')
    trash_data = os.path.join(trash_dir, 'trash-data')
    os.makedirs(tmp_dir)
    os.makedirs(data_dir)
    os.makedirs(trash_dir)

    for filepath in (a_data, b_data, trash_data):
        with open(filepath, 'w') as f:
            f.write(f.name)

    archive_path = os.path.abspath(os.path.join(tmp_dir, 'archive.tar.gz'))
    pack_dir(backup_dir, archive_path)
    with tarfile.open(archive_path) as tar:
        print(tar.getnames())
        assert Path(a_data).relative_to(tmp_dir).as_posix() in tar.getnames()
        assert Path(b_data).relative_to(tmp_dir).as_posix() in tar.getnames()
        assert Path(trash_data).relative_to(tmp_dir).as_posix() in \
            tar.getnames()

    cleaned_archive_path = os.path.abspath(
        os.path.join(tmp_dir, 'cleaned-archive.tar.gz')
    )
    pack_dir(backup_dir, cleaned_archive_path, exclude=(trash_dir,))
    with tarfile.open(cleaned_archive_path) as tar:
        assert Path(a_data).relative_to(tmp_dir).as_posix() in tar.getnames()
        assert Path(b_data).relative_to(tmp_dir).as_posix() in tar.getnames()
        assert Path(trash_data).relative_to(tmp_dir).as_posix() not in \
            tar.getnames()

    # Not absolute or unrelated path in exclude raises ValueError
    with pytest.raises(ValueError):
        pack_dir(backup_dir, cleaned_archive_path, exclude=('trash_data',))


def test_is_base_containers_alive(skale_base_containers):
    cont = skale_base_containers
    print([c.name for c in cont])
    assert is_base_containers_alive()


def test_is_base_containers_alive_one_failed(
    skale_base_containers_without_one
):
    assert not is_base_containers_alive()


def test_is_base_containers_alive_exited(skale_base_containers_exited):
    assert not is_base_containers_alive()


def test_is_base_containers_alive_empty():
    assert not is_base_containers_alive()
