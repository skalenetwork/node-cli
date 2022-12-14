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
  STATIC_PARAMS_FILEPATH,
  GLOBAL_SKALE_DIR,
  GLOBAL_SKALE_CONF_FILEPATH,
  REMOVED_CONTAINERS_FOLDER_PATH
)
from node_cli.configs import META_FILEPATH
from node_cli.configs.resource_allocation import RESOURCE_ALLOCATION_FILEPATH
from node_cli.utils.global_config import generate_g_config_file

from tests.helper import TEST_META_V1, TEST_META_V2


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
    with open(STATIC_PARAMS_FILEPATH, 'w') as f:
        yaml.dump(
            yaml.load(TEST_ENV_PARAMS, Loader=yaml.Loader),
            stream=f,
            Dumper=yaml.Dumper
        )
    yield STATIC_PARAMS_FILEPATH
    os.remove(STATIC_PARAMS_FILEPATH)


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


@pytest.fixture
def resource_alloc():
    with open(RESOURCE_ALLOCATION_FILEPATH, 'w') as alloc_file:
        json.dump({}, alloc_file)
    yield RESOURCE_ALLOCATION_FILEPATH
    os.remove(RESOURCE_ALLOCATION_FILEPATH)


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
def ensure_meta_removed():
    try:
        yield
    finally:
        if os.path.isfile(META_FILEPATH):
            os.remove(META_FILEPATH)
