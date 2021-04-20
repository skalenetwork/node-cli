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

import os
import mock
import yaml
import pytest

from node_cli.configs import (
  ENVIRONMENT_PARAMS_FILEPATH, GLOBAL_SKALE_DIR, GLOBAL_SKALE_CONF_FILEPATH
)
from node_cli.utils.global_config import generate_g_config_file


TEST_NET_PARAMS = """
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
            yaml.load(TEST_NET_PARAMS, Loader=yaml.Loader),
            stream=f,
            Dumper=yaml.Dumper
        )
    yield ENVIRONMENT_PARAMS_FILEPATH
    os.remove(ENVIRONMENT_PARAMS_FILEPATH)


@pytest.fixture()
def mocked_g_config():
    with mock.patch('os.path.expanduser', return_value='tests/'):
        generate_g_config_file(GLOBAL_SKALE_DIR, GLOBAL_SKALE_CONF_FILEPATH)
        yield
        generate_g_config_file(GLOBAL_SKALE_DIR, GLOBAL_SKALE_CONF_FILEPATH)
