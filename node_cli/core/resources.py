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

from node_cli.utils.schain_types import SchainTypes
from node_cli.utils.helper import write_json, read_json, run_cmd, format_output, safe_load_yml
from configs import ALLOCATION_FILEPATH
from node_cli.configs.resource_allocation import (
    RESOURCE_ALLOCATION_FILEPATH, TIMES, TIMEOUT,
    TEST_DIVIDER, SMALL_DIVIDER, MEDIUM_DIVIDER, LARGE_DIVIDER,
    MEMORY_FACTOR, DISK_FACTOR, DISK_MOUNTPOINT_FILEPATH,
    VOLUME_CHUNK, MAX_CPU_SHARES
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


class SChainVolumeAlloc():
    def __init__(self, disk_alloc: ResourceAlloc, proportions: dict):
        self.volume_alloc = {}
        disk_alloc_dict = disk_alloc.dict()
        for size_name in disk_alloc_dict:
            self.volume_alloc[size_name] = {}
            for key, value in proportions.items():
                lim = int(value * disk_alloc_dict[size_name])
                self.volume_alloc[size_name][key] = lim


def get_resource_allocation_info():
    try:
        return read_json(RESOURCE_ALLOCATION_FILEPATH)
    except FileNotFoundError:
        return None


def compose_resource_allocation_config():
    allocation_data = safe_load_yml(ALLOCATION_FILEPATH)
    schain_cpu_alloc, ima_cpu_alloc = get_cpu_alloc(allocation_data)
    schain_mem_alloc, ima_mem_alloc = get_memory_alloc(allocation_data)

    disk_alloc = get_disk_alloc()
    schain_volume_alloc = get_schain_volume_alloc(disk_alloc, allocation_data)
    return {
        'schain': {
            'cpu_shares': schain_cpu_alloc.dict(),
            'mem': schain_mem_alloc.dict(),
            'disk': disk_alloc.dict(),
            'volume_limits': schain_volume_alloc.volume_alloc,
            'storage_limit': get_storage_limit_alloc(allocation_data)
        },
        'ima': {
            'cpu_shares': ima_cpu_alloc.dict(),
            'mem': ima_mem_alloc.dict()
        }
    }


def get_schain_volume_alloc(disk_alloc: ResourceAlloc,
                            allocation_data: dict) -> SChainVolumeAlloc:
    proportions = get_schain_volume_proportions(allocation_data)
    return SChainVolumeAlloc(disk_alloc, proportions)


def get_schain_volume_proportions(allocation_data):
    return allocation_data['schain_proportions']['volume']


def get_storage_limit_alloc(allocation_data, testnet=False):
    network = 'testnet' if testnet else 'mainnet'
    return allocation_data[network]['storage_limit']


def generate_resource_allocation_config(force=False) -> None:
    if not force and os.path.isfile(RESOURCE_ALLOCATION_FILEPATH):
        msg = 'Resource allocation file is already exists'
        logger.debug(msg)
        print(msg)
        return
    logger.info('Generating resource allocation file ...')
    try:
        update_resource_allocation()
    except Exception as e:
        logger.exception(e)
        print('Can\'t generate resource allocation file, check out CLI logs')
    else:
        print(
            f'Resource allocation file generated: '
            f'{RESOURCE_ALLOCATION_FILEPATH}'
        )


def update_resource_allocation() -> None:
    resource_allocation_config = compose_resource_allocation_config()
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


def get_memory_alloc(allocation_data):
    mem_proportions = allocation_data['schain_proportions']['mem']
    available_memory = get_total_memory()

    schain_memory = mem_proportions['skaled'] * available_memory
    ima_memory = mem_proportions['ima'] * available_memory

    return ResourceAlloc(schain_memory), ResourceAlloc(ima_memory)


def get_cpu_alloc(allocation_data):
    cpu_proportions = allocation_data['schain_proportions']['cpu']
    schain_max_cpu_shares = int(cpu_proportions['skaled'] * MAX_CPU_SHARES)
    ima_max_cpu_shares = int(cpu_proportions['ima'] * MAX_CPU_SHARES)
    return (
        ResourceAlloc(schain_max_cpu_shares),
        ResourceAlloc(ima_max_cpu_shares)
    )


def get_disk_alloc():
    disk_path = get_disk_path()
    try:
        disk_size = get_disk_size(disk_path)
    except subprocess.CalledProcessError:
        raise Exception(
            "Couldn't get disk size, check disk mountpoint option."
        )
    free_space = int(disk_size * DISK_FACTOR) // VOLUME_CHUNK * VOLUME_CHUNK
    return ResourceAlloc(free_space)


def get_disk_size(disk_path):
    disk_size_cmd = construct_disk_size_cmd(disk_path)
    res = run_cmd(disk_size_cmd, shell=True)
    stdout, stderr = format_output(res)
    return int(stdout)


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
