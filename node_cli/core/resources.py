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
import logging
from time import sleep
from typing import Dict

import psutil

from node_cli.utils.docker_utils import ensure_volume
from node_cli.utils.schain_types import SchainTypes
from node_cli.utils.helper import (
    write_json, read_json, run_cmd, extract_env_params, safe_load_yml
)
from node_cli.configs import ALLOCATION_FILEPATH, STATIC_PARAMS_FILEPATH, SNAPSHOTS_SHARED_VOLUME
from node_cli.configs.resource_allocation import (
    RESOURCE_ALLOCATION_FILEPATH, TIMES, TIMEOUT,
    TEST_DIVIDER, SMALL_DIVIDER, MEDIUM_DIVIDER, LARGE_DIVIDER,
    MEMORY_FACTOR, MAX_CPU_SHARES
)

logger = logging.getLogger(__name__)


class NotEnoughDiskSpaceError(Exception):
    pass


class ResourceAlloc:
    def __init__(self, value, fractional=False):
        self.values = {
            'test4': value / TEST_DIVIDER,
            'test': value / TEST_DIVIDER,
            'small': value / SMALL_DIVIDER,
            'medium': value / MEDIUM_DIVIDER,
            'large': value / LARGE_DIVIDER
        }
        if not fractional:
            for k in self.values:
                self.values[k] = int(self.values[k])

    def dict(self):
        return self.values


def get_resource_allocation_info():
    try:
        return read_json(RESOURCE_ALLOCATION_FILEPATH)
    except FileNotFoundError:
        return None


def compose_resource_allocation_config(
    disk_device: str,
    env_type: str,
    params_by_env_type: Dict = None
) -> Dict:
    params_by_env_type = params_by_env_type or safe_load_yml(STATIC_PARAMS_FILEPATH)
    common_config = params_by_env_type['common']
    schain_cpu_alloc, ima_cpu_alloc = get_cpu_alloc(common_config)
    schain_mem_alloc, ima_mem_alloc = get_memory_alloc(common_config)
    schain_allocation_data = safe_load_yml(ALLOCATION_FILEPATH)

    return {
        'schain': {
            'cpu_shares': schain_cpu_alloc.dict(),
            'mem': schain_mem_alloc.dict(),
            'disk': schain_allocation_data[env_type]['disk'],
            'volume_limits': schain_allocation_data[env_type]['volume_limits'],  # noqa
            'leveldb_limits': schain_allocation_data[env_type]['leveldb_limits']  # noqa
        },
        'ima': {
            'cpu_shares': ima_cpu_alloc.dict(),
            'mem': ima_mem_alloc.dict()
        }
    }


def generate_resource_allocation_config(env_file, force=False) -> None:
    if not force and os.path.isfile(RESOURCE_ALLOCATION_FILEPATH):
        msg = 'Resource allocation file is already exists'
        logger.debug(msg)
        print(msg)
        return
    env_params = extract_env_params(env_file)
    if env_params is None:
        return
    logger.info('Generating resource allocation file ...')
    try:
        update_resource_allocation(
            env_params['DISK_MOUNTPOINT'],
            env_params['ENV_TYPE']
        )
    except Exception as e:
        logger.exception(e)
        print('Can\'t generate resource allocation file, check out CLI logs')
    else:
        print(
            f'Resource allocation file generated: '
            f'{RESOURCE_ALLOCATION_FILEPATH}'
        )


def update_resource_allocation(disk_device: str, env_type: str) -> None:
    resource_allocation_config = compose_resource_allocation_config(
        disk_device, env_type
    )
    write_json(RESOURCE_ALLOCATION_FILEPATH, resource_allocation_config)


def get_available_memory():
    memory = []
    for _ in range(0, TIMES):
        mem_info = psutil.virtual_memory()
        memory.append(mem_info.available)
        sleep(TIMEOUT)
    return sum(memory) / TIMES * MEMORY_FACTOR


def get_total_memory():
    memory = []
    for _ in range(0, TIMES):
        mem_info = psutil.virtual_memory()
        memory.append(mem_info.total)
        sleep(TIMEOUT)
    return sum(memory) / TIMES * MEMORY_FACTOR


def get_memory_alloc(common_config: Dict) -> ResourceAlloc:
    mem_proportions = common_config['schain']['mem']
    available_memory = get_total_memory()
    schain_memory = mem_proportions['skaled'] * available_memory
    ima_memory = mem_proportions['ima'] * available_memory
    return ResourceAlloc(schain_memory), ResourceAlloc(ima_memory)


def get_cpu_alloc(common_config: Dict) -> ResourceAlloc:
    cpu_proportions = common_config['schain']['cpu']
    schain_max_cpu_shares = int(cpu_proportions['skaled'] * MAX_CPU_SHARES)
    ima_max_cpu_shares = int(cpu_proportions['ima'] * MAX_CPU_SHARES)
    return (
        ResourceAlloc(schain_max_cpu_shares),
        ResourceAlloc(ima_max_cpu_shares)
    )


def verify_disk_size(
    disk_device: str,
    env_configs: dict,
) -> Dict:
    disk_size = get_disk_size(disk_device)
    env_disk_size = env_configs['server']['disk']
    check_disk_size(disk_size, env_disk_size)


def check_disk_size(disk_size: int, env_disk_size: int):
    if env_disk_size > disk_size:
        raise NotEnoughDiskSpaceError(
            f'Disk size: {disk_size}, required disk size: {env_disk_size}'
        )


def get_disk_size(disk_device: str) -> int:
    disk_size_cmd = construct_disk_size_cmd(disk_device)
    output = run_cmd(disk_size_cmd).stdout.decode('utf-8')
    return int(output)


def construct_disk_size_cmd(disk_path: str) -> list:
    return ['blockdev', '--getsize64', disk_path]


def check_is_partition(disk_path):
    res = run_cmd(['blkid', disk_path])
    output = str(res.stdout)
    if 'PARTUUID' in output:
        return True
    return False


def get_allocation_option_name(schain):
    part_of_node = int(schain['partOfNode'])
    return SchainTypes(part_of_node).name


def init_shared_space_volume(env_type):
    logger.info('Configuring shared space volume')
    schain_allocation_data = safe_load_yml(ALLOCATION_FILEPATH)
    size = schain_allocation_data[env_type]['shared_space']
    ensure_volume(SNAPSHOTS_SHARED_VOLUME, size)
