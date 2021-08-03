import filecmp
import json
import os
import pathlib
import shutil

import pytest

from node_cli.core.host2.docker_config import (
    DockerConfigResult,
    ensure_docker_service_config_dir,
    ensure_service_overriden_config,
    ensure_docker_daemon_config,
    link_socket_to_default_path,
    NoSocketFileError,
    OverridenConfigExsitsError
)


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
            ['[Service]', 'ExecStart=', 'ExecStart=/usr/bin/dockerd']
        )
    assert r == DockerConfigResult.CHANGED

    r = ensure_service_overriden_config(overriden_config_path)
    with open(overriden_config_path) as overriden_config_file:
        assert overriden_config_file.read() == '\n'.join(
            ['[Service]', 'ExecStart=', 'ExecStart=/usr/bin/dockerd']
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
        assert conf['hosts'] == ['unix:///var/lib/skale/docker.sock']
    assert r == DockerConfigResult.CHANGED

    conf.pop('hosts')
    conf['test'] = 'TEST'
    with open(daemon_config_path, 'w') as daemon_config_file:
        json.dump(conf, daemon_config_file)

    r = ensure_docker_daemon_config(daemon_config_path)
    with open(daemon_config_path, 'r') as daemon_config_file:
        conf = json.load(daemon_config_file)
        assert conf['live-restore'] is True
        assert conf['hosts'] == ['unix:///var/lib/skale/docker.sock']
        assert conf['test'] == 'TEST'
    assert r == DockerConfigResult.CHANGED


def test_link_socket_to_default_path(tmp_dir):
    socket_path = os.path.join(tmp_dir, 'new.socket')
    default_path = os.path.join(tmp_dir, 'default.socket')

    with pytest.raises(NoSocketFileError):
        link_socket_to_default_path(socket_path, default_path)

    pathlib.Path(socket_path).touch()
    r = link_socket_to_default_path(socket_path, default_path)
    assert os.path.islink(default_path)
    assert filecmp.cmp(socket_path, default_path)
    assert r == DockerConfigResult.CHANGED
