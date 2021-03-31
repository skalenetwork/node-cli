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
import subprocess
from time import sleep

import psutil

from tools.schain_types import SchainTypes
from tools.helper import write_json, read_json, run_cmd, format_output, extract_env_params
from core.helper import safe_load_yml
from core.configs_reader import get_config_env_schain_option
from configs import ALLOCATION_FILEPATH, CONFIGS_FILEPATH
from configs.resource_allocation import (
    RESOURCE_ALLOCATION_FILEPATH, TIMES, TIMEOUT,
    TEST_DIVIDER, SMALL_DIVIDER, MEDIUM_DIVIDER, LARGE_DIVIDER,
    MEMORY_FACTOR, DISK_MOUNTPOINT_FILEPATH, MAX_CPU_SHARES
)

logger = logging.getLogger(__name__)


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


def compose_resource_allocation_config(env_type):
    net_configs = safe_load_yml(CONFIGS_FILEPATH)
    schain_allocation_data = safe_load_yml(ALLOCATION_FILEPATH)

    print(schain_allocation_data)
    schain_cpu_alloc, ima_cpu_alloc = get_cpu_alloc(net_configs)
    schain_mem_alloc, ima_mem_alloc = get_memory_alloc(net_configs)

    disk_alloc = get_static_disk_alloc(env_type)
    # schain_volume_alloc = get_schain_volume_alloc(disk_alloc, allocation_data)

    # todo!!!!!!!

    return {
        'schain': {
            'cpu_shares': schain_cpu_alloc.dict(),
            'mem': schain_mem_alloc.dict(),
            'disk': disk_alloc.dict(),
            # 'volume_limits': schain_volume_alloc.volume_alloc,
            # 'storage_limit': get_storage_limit_alloc(allocation_data)
        },
        'ima': {
            'cpu_shares': ima_cpu_alloc.dict(),
            'mem': ima_mem_alloc.dict()
        }
    }


def get_schain_volume_proportions(allocation_data):
    return allocation_data['schain_proportions']['volume']


def get_storage_limit_alloc(allocation_data, testnet=False):
    network = 'testnet' if testnet else 'mainnet'
    return allocation_data[network]['storage_limit']


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
        update_resource_allocation(env_params['ENV_TYPE'])
    except Exception as e:
        logger.exception(e)
        print('Can\'t generate resource allocation file, check out CLI logs')
    else:
        print(
            f'Resource allocation file generated: '
            f'{RESOURCE_ALLOCATION_FILEPATH}'
        )


def update_resource_allocation(env_type) -> None:
    resource_allocation_config = compose_resource_allocation_config(env_type)
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


def get_memory_alloc(net_configs):
    mem_proportions = net_configs['common']['schain']['mem']
    available_memory = get_total_memory()
    schain_memory = mem_proportions['skaled'] * available_memory
    ima_memory = mem_proportions['ima'] * available_memory
    return ResourceAlloc(schain_memory), ResourceAlloc(ima_memory)


def get_cpu_alloc(net_configs):
    cpu_proportions = net_configs['common']['schain']['cpu']
    schain_max_cpu_shares = int(cpu_proportions['skaled'] * MAX_CPU_SHARES)
    ima_max_cpu_shares = int(cpu_proportions['ima'] * MAX_CPU_SHARES)
    return (
        ResourceAlloc(schain_max_cpu_shares),
        ResourceAlloc(ima_max_cpu_shares)
    )


def get_static_disk_alloc(env_type: str):
    disk_size = get_disk_size()
    env_disk_size = get_config_env_schain_option(env_type, 'disk_size_bytes')
    check_disk_size(disk_size, env_disk_size)
    # free_space = calculate_free_disk_space(env_disk_size)
    # return ResourceAlloc(free_space)


def check_disk_size(disk_size: int, env_disk_size: int):
    if env_disk_size > disk_size:
        raise Exception(f'Disk size: {disk_size}, required disk size: {env_disk_size}')


def get_disk_size():
    disk_path = get_disk_path()
    disk_size_cmd = construct_disk_size_cmd(disk_path)
    try:
        res = run_cmd(disk_size_cmd, shell=True)
        stdout, _ = format_output(res)
        return int(stdout)
    except subprocess.CalledProcessError:
        raise Exception(
            "Couldn't get disk size, check disk mountpoint option."
        )


def construct_disk_size_cmd(disk_path):
    return f'sudo blockdev --getsize64 {disk_path}'


def check_is_partition(disk_path):
    res = run_cmd(['blkid', disk_path])
    output = str(res.stdout)
    if 'PARTUUID' in output:
        return True
    return False


def get_allocation_option_name(schain):
    part_of_node = int(schain['partOfNode'])
    return SchainTypes(part_of_node).name


def get_disk_path():
    f = open(DISK_MOUNTPOINT_FILEPATH, "r")
    return f.read()
