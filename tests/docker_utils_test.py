import os
import time
from time import sleep
from unittest.mock import MagicMock

import mock
import pytest

from node_cli.utils.docker_utils import (
    docker_cleanup,
    get_all_ima_containers,
    get_all_skaled_containers,
    rm_legacy_containers,
    save_container_logs,
    safe_rm,
)
from node_cli.configs import REMOVED_CONTAINERS_FOLDER_PATH


@pytest.fixture
def simple_container(dclient, simple_image, docker_hc):
    name = 'simple-container'
    c = None
    try:
        info = dclient.api.create_container(
            simple_image, detach=True, name=name, host_config=docker_hc
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
        'INFO:__main__:Waiting\n',
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
        'INFO:__main__:Waiting\n',
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

    with mock.patch('node_cli.utils.docker_utils.run_cmd', side_effect=ValueError):
        docker_cleanup(dclient=dclient)


def _make_container(name: str) -> MagicMock:
    c = MagicMock()
    c.name = name
    c.id = name
    return c


def test_get_all_skaled_containers_real(dclient):
    containers = []
    names = ['sk_skaled_test_chain', 'skale_schain_test_chain']
    try:
        for name in names:
            c = dclient.containers.run('alpine', 'true', name=name, detach=True)
            containers.append(c)
        for c in containers:
            c.wait()
        result = get_all_skaled_containers()
        result_names = {c.name for c in result}
        for name in names:
            assert name in result_names
    finally:
        for c in containers:
            try:
                c.remove(force=True)
            except Exception:
                pass


def test_get_all_skaled_containers_both_prefixes():
    new_container = _make_container('sk_skaled_chain1')
    legacy_container = _make_container('skale_schain_chain2')

    def fake_list(all=True, filters=None):
        prefix = filters['name']
        if prefix == 'sk_skaled_':
            return [new_container]
        if prefix == 'skale_schain_':
            return [legacy_container]
        return []

    mock_dc = MagicMock()
    mock_dc.containers.list.side_effect = fake_list

    with mock.patch('node_cli.utils.docker_utils.docker_client', return_value=mock_dc):
        result = get_all_skaled_containers()

    assert len(result) == 2
    names = {c.name for c in result}
    assert names == {'sk_skaled_chain1', 'skale_schain_chain2'}


def test_get_all_ima_containers_both_prefixes():
    new_container = _make_container('sk_ima_chain1')
    legacy_container = _make_container('skale_ima_chain2')

    def fake_list(all=True, filters=None):
        prefix = filters['name']
        if prefix == 'sk_ima_':
            return [new_container]
        if prefix == 'skale_ima_':
            return [legacy_container]
        return []

    mock_dc = MagicMock()
    mock_dc.containers.list.side_effect = fake_list

    with mock.patch('node_cli.utils.docker_utils.docker_client', return_value=mock_dc):
        result = get_all_ima_containers()

    assert len(result) == 2
    names = {c.name for c in result}
    assert names == {'sk_ima_chain1', 'skale_ima_chain2'}


def test_rm_legacy_containers(dclient):
    names = ['skale_sync_admin', 'skale_api', 'skale_schain_old']
    containers = []
    try:
        for name in names:
            c = dclient.containers.run('alpine', 'true', name=name, detach=True)
            containers.append(c)
        for c in containers:
            c.wait()

        rm_legacy_containers()

        remaining = dclient.containers.list(all=True, filters={'name': 'skale_'})
        remaining_names = {c.name for c in remaining}
        for name in names:
            assert name not in remaining_names
    finally:
        for c in containers:
            try:
                c.remove(force=True)
            except Exception:
                pass
