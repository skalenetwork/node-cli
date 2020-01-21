#   -*- coding: utf-8 -*-
#
#   This file is part of skale-node-cli
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
from configs import NODE_DATA_PATH, THIRDPARTY_FOLDER_PATH, DATAFILES_FOLDER

MEDIUM_DIVIDER = 1
SMALL_DIVIDER = 8
TINY_DIVIDER = 128

TIMES = 1
TIMEOUT = 1
MEMORY_FACTOR = 0.9
DISK_FACTOR = 0.95

VOLUME_CHUNK = 512 * TINY_DIVIDER

RESOURCE_ALLOCATION_FILENAME = 'resource_allocation.json'
RESOURCE_ALLOCATION_FILEPATH = os.path.join(NODE_DATA_PATH, RESOURCE_ALLOCATION_FILENAME)

DISK_MOUNTPOINT_FILENAME = 'disk_mountpoint.txt'
DISK_MOUNTPOINT_FILEPATH = os.path.join(NODE_DATA_PATH, DISK_MOUNTPOINT_FILENAME)

SGX_SERVER_URL_FILENAME = 'sgx_server_url.txt'
SGX_SERVER_URL_FILEPATH = os.path.join(NODE_DATA_PATH, SGX_SERVER_URL_FILENAME)

CONVOY_HELPER_SCRIPT_FILENAME = 'dm_dev_partition.sh'
CONVOY_HELPER_SCRIPT_FILEPATH = os.path.join(THIRDPARTY_FOLDER_PATH, CONVOY_HELPER_SCRIPT_FILENAME)

CONVOY_SERVICE_TEMPLATE_FILENAME = 'convoy.service.j2'
CONVOY_SERVICE_TEMPLATE_PATH = os.path.join(DATAFILES_FOLDER, CONVOY_SERVICE_TEMPLATE_FILENAME)
CONVOY_SERVICE_PATH = '/etc/systemd/system/convoy.service'
