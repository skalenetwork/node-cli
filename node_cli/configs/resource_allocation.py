#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
#
#   Copyright (C) 2019 SKALE Labs
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
from node_cli.configs import NODE_DATA_PATH

LARGE_DIVIDER = 1
MEDIUM_DIVIDER = 8
TEST_DIVIDER = 8
SMALL_DIVIDER = 128

TIMES = 1
TIMEOUT = 1
MEMORY_FACTOR = 0.8
DISK_FACTOR = 0.95

MAX_CPU_SHARES = 1024

VOLUME_CHUNK = 512 * SMALL_DIVIDER

RESOURCE_ALLOCATION_FILENAME = 'resource_allocation.json'
RESOURCE_ALLOCATION_FILEPATH = os.path.join(NODE_DATA_PATH, RESOURCE_ALLOCATION_FILENAME)

SGX_SERVER_URL_FILENAME = 'sgx_server_url.txt'
SGX_SERVER_URL_FILEPATH = os.path.join(NODE_DATA_PATH, SGX_SERVER_URL_FILENAME)
