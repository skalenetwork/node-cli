import json
import os
import pathlib
import shutil
from contextlib import contextmanager
from timeit import default_timer as timer

import docker
import pytest

from node_cli.core.docker_config import (
    assert_no_containers,
    ContainersExistError,
    DockerConfigResult,
    ensure_docker_daemon_config,
    ensure_docker_service_config_dir,
    ensure_run_dir,
    ensure_service_overriden_config,
    OverridenConfigExsitsError,
    SocketInitTimeoutError,
    wait_for_socket_initialization
)


@contextmanager
def in_time(seconds):
    start_ts = timer()
    yield
    ts_diff = timer() - start_ts
    assert ts_diff < seconds, (ts_diff, seconds)


@pytest.fixture
def tmp_dir():
    test_home_dir_path = os.getenv('TEST_HOME_DIR')
    tmp_dir_path = os.path.join(test_home_dir_path, 'tmp')
    try:
        os.makedirs(tmp_dir_path, exist_ok=True)
        yield tmp_dir_path
    finally:
        shutil.rmtree(tmp_dir_path)


def test_ensure_docker_service_config_dir(tmp_dir):
    service_config_dir = os.path.join(tmp_dir, 'docker.service.d')
    r = ensure_docker_service_config_dir(service_config_dir)
    assert os.path.isdir(service_config_dir)
    assert r == DockerConfigResult.CHANGED

    r = ensure_docker_service_config_dir(service_config_dir)
    assert os.path.isdir(service_config_dir)
    assert r == DockerConfigResult.UNCHANGED


def test_ensure_service_overriden_config(tmp_dir):
    overriden_config_path = os.path.join(tmp_dir, 'override.conf')
    r = ensure_service_overriden_config(overriden_config_path)
    with open(overriden_config_path) as overriden_config_file:
        assert overriden_config_file.read() == '\n'.join(
            [
                '[Service]',
                'ExecStart=',
                'ExecStart=/usr/bin/dockerd',
                'ExecStartPre=/bin/mkdir -p /var/run/skale'
            ]
        )
    assert r == DockerConfigResult.CHANGED

    r = ensure_service_overriden_config(overriden_config_path)
    with open(overriden_config_path) as overriden_config_file:
        assert overriden_config_file.read() == '\n'.join(
            [
                '[Service]',
                'ExecStart=',
                'ExecStart=/usr/bin/dockerd',
                'ExecStartPre=/bin/mkdir -p /var/run/skale'
            ]
        )
    assert r == DockerConfigResult.UNCHANGED

    with open(overriden_config_path, 'w') as overriden_config_file:
        overriden_config_file.write('Could it be more useless?')

    with pytest.raises(OverridenConfigExsitsError):
        ensure_service_overriden_config(overriden_config_path)


def test_ensure_docker_daemon_config(tmp_dir):
    daemon_config_path = os.path.join(tmp_dir, 'daemon.json')
    r = ensure_docker_daemon_config(daemon_config_path)

    with open(daemon_config_path, 'r') as daemon_config_file:
        conf = json.load(daemon_config_file)
        assert conf['live-restore'] is True
        assert conf['hosts'] == [
            'fd://',
            'unix:///var/run/skale/docker.sock'
        ]
    assert r == DockerConfigResult.CHANGED

    conf.pop('hosts')
    conf['test'] = 'TEST'
    with open(daemon_config_path, 'w') as daemon_config_file:
        json.dump(conf, daemon_config_file)

    r = ensure_docker_daemon_config(daemon_config_path)
    with open(daemon_config_path, 'r') as daemon_config_file:
        conf = json.load(daemon_config_file)
        assert conf['live-restore'] is True
        assert conf['hosts'] == [
            'fd://',
            'unix:///var/run/skale/docker.sock'
        ]
        assert conf['test'] == 'TEST'
    assert r == DockerConfigResult.CHANGED


def test_ensure_run_dir(tmp_dir):
    run_dir = os.path.join(tmp_dir, 'run')
    r = ensure_run_dir(run_dir)
    assert os.path.isdir(run_dir)
    assert r == DockerConfigResult.CHANGED

    r = ensure_run_dir(run_dir)
    assert os.path.isdir(run_dir)
    assert r == DockerConfigResult.UNCHANGED


@pytest.fixture
def container():
    client = docker.from_env()
    c = client.containers.run('hello-world', detach=True)
    yield c
    c.remove(force=True)


def test_assert_no_contaners():
    assert_no_containers(ignore=('ganache',))


def test_assert_no_containers_failed(container):
    with pytest.raises(ContainersExistError):
        assert_no_containers()


def test_wait_for_socket_initialization(tmp_dir):
    socket_path = os.path.join(tmp_dir, 'd.socket')
    with in_time(8):
        with pytest.raises(SocketInitTimeoutError):
            wait_for_socket_initialization(socket_path, allowed_time=5)
    pathlib.Path(socket_path).touch()
    with in_time(1):
        wait_for_socket_initialization(socket_path)
