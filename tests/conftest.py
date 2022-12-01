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
""" SKALE config test """

import json
import os
import pathlib
import shutil

import docker
import mock
import pytest
import yaml

from node_cli.configs import (
    ENVIRONMENT_PARAMS_FILEPATH, GLOBAL_SKALE_DIR, GLOBAL_SKALE_CONF_FILEPATH,
    REMOVED_CONTAINERS_FOLDER_PATH, NGINX_CONTAINER_NAME
)
from node_cli.configs.node_options import NODE_OPTIONS_FILEPATH, NODE_OPTIONS_LOCK_PATH
from node_cli.utils.global_config import generate_g_config_file
from node_cli.configs.resource_allocation import RESOURCE_ALLOCATION_FILEPATH
from node_cli.configs.ssl import SSL_FOLDER_PATH
from node_cli.utils.docker_utils import docker_client


TEST_ENV_PARAMS = """
mainnet:
  server:
    cpu_total: 4
    cpu_physical: 4
    memory: 32
    swap: 16
    disk: 2000000000000

  packages:
    docker: 1.1.3
    docker-compose: 1.1.3
    iptables-persistant: 1.1.3
    lvm2: 1.1.1

testnet:
  server:
    cpu_total: 4
    cpu_physical: 4
    memory: 32
    swap: 16
    disk: 200000000000

  packages:
    docker: 1.1.3
    docker-compose: 1.1.3
    iptables-persistant: 1.1.3
    lvm2: 1.1.1

testnet:
  server:
    cpu_total: 4
    cpu_physical: 4
    memory: 32
    swap: 16
    disk: 200000000000

  packages:
    docker: 1.1.3
    docker-compose: 1.1.3
    iptables-persistant: 1.1.3
    lvm2: 1.1.1

qanet:
  server:
    cpu_total: 4
    cpu_physical: 4
    memory: 32
    swap: 16
    disk: 200000000000

  packages:
    docker: 1.1.3
    docker-compose: 1.1.3
    iptables-persistant: 1.1.3
    lvm2: 1.1.1

devnet:
  server:
    cpu_total: 4
    cpu_physical: 4
    memory: 32
    swap: 16
    disk: 80000000000

  packages:
    iptables-persistant: 1.1.3
    lvm2: 1.1.1
    docker-compose: 1.1.3

  docker:
    docker-api: 1.1.3
    docker-engine: 1.1.3
"""


@pytest.fixture
def net_params_file():
    with open(ENVIRONMENT_PARAMS_FILEPATH, 'w') as f:
        yaml.dump(
            yaml.load(TEST_ENV_PARAMS, Loader=yaml.Loader),
            stream=f,
            Dumper=yaml.Dumper
        )
    yield ENVIRONMENT_PARAMS_FILEPATH
    os.remove(ENVIRONMENT_PARAMS_FILEPATH)


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
        dclient.images.build(
            tag=name,
            rm=True,
            nocache=True,
            path='tests/simple_container'
        )
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
        log_config=docker.types.LogConfig(
            type=docker.types.LogConfig.types.JSON
        )
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
    pathlib.Path(NODE_OPTIONS_LOCK_PATH).unlink(missing_ok=True)
    yield
    pathlib.Path(NODE_OPTIONS_FILEPATH).unlink(missing_ok=True)
    pathlib.Path(NODE_OPTIONS_LOCK_PATH).unlink(missing_ok=True)


def clean_node_data():
    pass


@pytest.fixture
def resource_alloc():
    with open(RESOURCE_ALLOCATION_FILEPATH, 'w') as alloc_file:
        json.dump({}, alloc_file)
    yield RESOURCE_ALLOCATION_FILEPATH
    os.remove(RESOURCE_ALLOCATION_FILEPATH)


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
            volumes={
                ssl_folder: {
                    'bind': '/ssl',
                    'mode': 'ro',
                    'propagation': 'slave'
                }
            }
        )
        yield c
    finally:
        if c is not None:
            try:
                c.remove(force=True)
            except Exception:
                pass
