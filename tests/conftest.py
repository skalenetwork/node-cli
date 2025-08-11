#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
#
#   Copyright (C) 2019 SKALE Labs
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Lesser General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Lesser General Public License for more details.
#
#   You should have received a copy of the GNU Lesser General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

import json
import os
import pathlib
import shutil
import tempfile
from contextlib import contextmanager

import docker
import mock
import pytest
import redis

from node_cli.configs import (
    CONTAINER_CONFIG_TMP_PATH,
    GLOBAL_SKALE_CONF_FILEPATH,
    GLOBAL_SKALE_DIR,
    META_FILEPATH,
    NGINX_CONFIG_FILEPATH,
    NGINX_CONTAINER_NAME,
    REDIS_URI,
    REMOVED_CONTAINERS_FOLDER_PATH,
    SCHAIN_NODE_DATA_PATH,
)
from node_cli.configs.node_options import NODE_OPTIONS_FILEPATH
from node_cli.configs.resource_allocation import RESOURCE_ALLOCATION_FILEPATH
from node_cli.configs.ssl import SSL_FOLDER_PATH
from node_cli.core.node_options import NodeOptions
from node_cli.utils.docker_utils import docker_client
from node_cli.utils.global_config import generate_g_config_file
from node_cli.utils.node_type import NodeMode
from tests.helper import TEST_META_V1, TEST_META_V2, TEST_META_V3, TEST_SCHAINS_MNT_DIR_SINGLE_CHAIN


@pytest.fixture()
def tmp_dir_path():
    plain_path = 'tests/tmp/'
    path = pathlib.Path(plain_path)
    path.mkdir(parents=True)
    try:
        yield plain_path
    finally:
        shutil.rmtree(path)


@pytest.fixture()
def removed_containers_folder():
    path = pathlib.Path(REMOVED_CONTAINERS_FOLDER_PATH)
    path.mkdir(parents=True, exist_ok=True)
    try:
        yield REMOVED_CONTAINERS_FOLDER_PATH
    finally:
        shutil.rmtree(path)


@pytest.fixture()
def dclient():
    return docker.from_env()


@pytest.fixture()
def simple_image(dclient):
    name = 'simple-image'
    try:
        dclient.images.build(tag=name, rm=True, nocache=True, path='tests/simple_container')
        yield name
    finally:
        try:
            dclient.images.get(name)
        except docker.errors.ImageNotFound:
            return
        dclient.images.remove(name, force=True)


@pytest.fixture()
def docker_hc(dclient):
    dclient = docker.from_env()
    return dclient.api.create_host_config(
        log_config=docker.types.LogConfig(type=docker.types.LogConfig.types.JSON)
    )


@pytest.fixture()
def mocked_g_config():
    with mock.patch('os.path.expanduser', return_value='tests/'):
        generate_g_config_file(GLOBAL_SKALE_DIR, GLOBAL_SKALE_CONF_FILEPATH)
        yield
        generate_g_config_file(GLOBAL_SKALE_DIR, GLOBAL_SKALE_CONF_FILEPATH)


@pytest.fixture()
def clean_node_options():
    pathlib.Path(NODE_OPTIONS_FILEPATH).unlink(missing_ok=True)
    try:
        yield
    finally:
        pathlib.Path(NODE_OPTIONS_FILEPATH).unlink(missing_ok=True)


@pytest.fixture
def resource_alloc():
    with open(RESOURCE_ALLOCATION_FILEPATH, 'w') as alloc_file:
        json.dump({}, alloc_file)
    yield RESOURCE_ALLOCATION_FILEPATH
    os.remove(RESOURCE_ALLOCATION_FILEPATH)


@pytest.fixture
def inited_node():
    path = pathlib.Path(NGINX_CONFIG_FILEPATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()
    try:
        yield
    finally:
        os.remove(NGINX_CONFIG_FILEPATH)


@pytest.fixture
def ssl_folder():
    if os.path.isdir(SSL_FOLDER_PATH):
        shutil.rmtree(SSL_FOLDER_PATH)
    path = pathlib.Path(SSL_FOLDER_PATH)
    path.mkdir(parents=True, exist_ok=True)
    try:
        yield
    finally:
        shutil.rmtree(SSL_FOLDER_PATH)


@pytest.fixture
def active_node_option():
    node_options = NodeOptions()
    node_options.node_mode = NodeMode.ACTIVE
    try:
        yield
    finally:
        shutil.rmtree(NODE_OPTIONS_FILEPATH)


@pytest.fixture
def passive_node_option():
    node_options = NodeOptions()
    node_options.node_mode = NodeMode.PASSIVE
    try:
        yield
    finally:
        shutil.rmtree(NODE_OPTIONS_FILEPATH)


@pytest.fixture
def dutils():
    return docker_client()


@pytest.fixture
def nginx_container(dutils, ssl_folder):
    c = None
    try:
        c = dutils.containers.run(
            'nginx:1.20.2',
            name=NGINX_CONTAINER_NAME,
            detach=True,
            volumes={ssl_folder: {'bind': '/ssl', 'mode': 'ro', 'propagation': 'slave'}},
        )
        yield c
    finally:
        if c is not None:
            try:
                c.remove(force=True)
            except Exception:
                pass


@pytest.fixture
def meta_file_v1():
    with open(META_FILEPATH, 'w') as f:
        json.dump(TEST_META_V1, f)
    try:
        yield META_FILEPATH
    finally:
        os.remove(META_FILEPATH)


@pytest.fixture
def meta_file_v2():
    with open(META_FILEPATH, 'w') as f:
        json.dump(TEST_META_V2, f)
    try:
        yield META_FILEPATH
    finally:
        os.remove(META_FILEPATH)


@pytest.fixture
def meta_file_v3():
    with open(META_FILEPATH, 'w') as f:
        json.dump(TEST_META_V3, f)
    try:
        yield META_FILEPATH
    finally:
        os.remove(META_FILEPATH)


@pytest.fixture
def ensure_meta_removed():
    try:
        yield
    finally:
        if os.path.isfile(META_FILEPATH):
            os.remove(META_FILEPATH)


@pytest.fixture
def tmp_config_dir():
    os.mkdir(CONTAINER_CONFIG_TMP_PATH)
    try:
        yield CONTAINER_CONFIG_TMP_PATH
    finally:
        shutil.rmtree(CONTAINER_CONFIG_TMP_PATH)


@pytest.fixture
def tmp_schains_dir():
    os.makedirs(SCHAIN_NODE_DATA_PATH, exist_ok=True)
    try:
        yield SCHAIN_NODE_DATA_PATH
    finally:
        shutil.rmtree(SCHAIN_NODE_DATA_PATH)


@pytest.fixture
def tmp_passive_datadir():
    os.makedirs(TEST_SCHAINS_MNT_DIR_SINGLE_CHAIN, exist_ok=True)
    try:
        yield TEST_SCHAINS_MNT_DIR_SINGLE_CHAIN
    finally:
        shutil.rmtree(TEST_SCHAINS_MNT_DIR_SINGLE_CHAIN)


@pytest.fixture
def valid_env_params():
    return {
        'ENDPOINT': 'http://localhost:8545',
        'IMA_ENDPOINT': 'http://127.0.01',
        'DB_USER': 'user',
        'DB_PASSWORD': 'pass',
        'DB_PORT': '3307',
        'NODE_VERSION': 'master',
        'FILEBEAT_HOST': '127.0.0.1:3010',
        'SGX_SERVER_URL': 'http://127.0.0.1',
        'DISK_MOUNTPOINT': '/dev/sss',
        'DOCKER_LVMPY_STREAM': 'master',
        'ENV_TYPE': 'devnet',
        'SCHAIN_NAME': 'test',
        'ENFORCE_BTRFS': 'False',
        'MANAGER_CONTRACTS': 'test-manager',
        'IMA_CONTRACTS': 'test-ima',
    }


@pytest.fixture
def valid_env_file(valid_env_params):
    file_name = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            for key, value in valid_env_params.items():
                f.write(f'{key}={value}\n')
            file_name = f.name
        yield file_name
    finally:
        if file_name:
            os.unlink(file_name)


@pytest.fixture
def mock_chain_response():
    return {
        'jsonrpc': '2.0',
        'id': 1,
        'result': '0x1',
    }


@pytest.fixture
def mock_networks_metadata():
    return {
        'networks': [
            {'chainId': 1, 'name': 'Mainnet', 'path': 'mainnet'},
            {'chainId': 2, 'name': 'Testnet', 'path': 'testnet'},
        ]
    }


@contextmanager
def set_env_var(name, value):
    old_value = os.environ.get(name)
    os.environ[name] = value
    try:
        yield
    finally:
        if old_value is None:
            del os.environ[name]
        else:
            os.environ[name] = old_value


@pytest.fixture
def regular_user_conf(tmp_path):
    test_env_path = pathlib.Path(tmp_path / 'test-env')
    try:
        test_env = """
        ENDPOINT=http://localhost:8545
        NODE_VERSION='main'
        FILEBEAT_HOST=127.0.0.1:3010
        SGX_SERVER_URL=http://127.0.0.1
        DISK_MOUNTPOINT=/dev/sss
        DOCKER_LVMPY_STREAM='master'
        ENV_TYPE='devnet'
        MANAGER_CONTRACTS='test-manager'
        IMA_CONTRACTS='test-ima'
        """
        with open(test_env_path, 'w') as env_file:
            env_file.write(test_env)
        yield test_env_path
    finally:
        test_env_path.unlink()


@pytest.fixture
def fair_user_conf(tmp_path):
    test_env_path = pathlib.Path(tmp_path / 'test-env')
    try:
        test_env = """
        BOOT_ENDPOINT=http://localhost:8545
        NODE_VERSION='main'
        FILEBEAT_HOST=127.0.0.1:3010
        SGX_SERVER_URL=http://127.0.0.1
        DISK_MOUNTPOINT=/dev/sss
        ENV_TYPE='devnet'
        ENFORCE_BTRFS=False
        FAIR_CONTRACTS='test-fair'
        """
        with open(test_env_path, 'w') as env_file:
            env_file.write(test_env)
        yield test_env_path
    finally:
        test_env_path.unlink()


@pytest.fixture
def fair_boot_user_conf(tmp_path):
    test_env_path = pathlib.Path(tmp_path / 'test-env')
    try:
        test_env = """
        ENDPOINT=http://localhost:8545
        NODE_VERSION='main'
        FILEBEAT_HOST=127.0.0.1:3010
        SGX_SERVER_URL=http://127.0.0.1
        DISK_MOUNTPOINT=/dev/sss
        ENV_TYPE='devnet'
        MANAGER_CONTRACTS='test-manager'
        IMA_CONTRACTS='test-ima'
        """
        with open(test_env_path, 'w') as env_file:
            env_file.write(test_env)
        yield test_env_path
    finally:
        test_env_path.unlink()


@pytest.fixture
def passive_user_conf(tmp_path):
    test_env_path = pathlib.Path(tmp_path / 'test-env')
    try:
        test_env = """
        ENDPOINT=http://localhost:8545
        NODE_VERSION='main'
        FILEBEAT_HOST=127.0.0.1:3010
        DISK_MOUNTPOINT=/dev/sss
        ENV_TYPE='devnet'
        SCHAIN_NAME='test-schain'
        ENFORCE_BTRFS=False
        MANAGER_CONTRACTS='test-manager'
        """
        with open(test_env_path, 'w') as env_file:
            env_file.write(test_env)
        yield test_env_path
    finally:
        test_env_path.unlink()


@pytest.fixture
def redis_client():
    cpool = redis.ConnectionPool.from_url(REDIS_URI)
    return redis.Redis(connection_pool=cpool)
