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
import logging
import subprocess
from time import sleep

import psutil

from tools.schain_types import SchainTypes
from tools.helper import write_json, read_json, run_cmd, format_output
from core.helper import safe_load_yml, to_camel_case
from configs import ALLOCATION_FILEPATH
from configs.resource_allocation import RESOURCE_ALLOCATION_FILEPATH, TIMES, TIMEOUT, \
    TINY_DIVIDER, TEST_DIVIDER, SMALL_DIVIDER, MEDIUM_DIVIDER, MEMORY_FACTOR, DISK_FACTOR, \
    DISK_MOUNTPOINT_FILEPATH, VOLUME_CHUNK

logger = logging.getLogger(__name__)

ALLOCATION_DATA = safe_load_yml(ALLOCATION_FILEPATH)


class ResourceAlloc:
    def __init__(self, value, fractional=False):
        self.values = {
            'part_test4': value / TEST_DIVIDER,
            'part_test': value / TEST_DIVIDER,
            'part_small': value / TINY_DIVIDER,
            'part_medium': value / SMALL_DIVIDER,
            'part_large': value / MEDIUM_DIVIDER
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
                self.volume_alloc[size_name][to_camel_case(key)] = lim


def get_resource_allocation_info():
    try:
        return read_json(RESOURCE_ALLOCATION_FILEPATH)
    except FileNotFoundError:
        return None


def generate_resource_allocation_config():
    cpu_alloc = get_cpu_alloc()
    mem_alloc = get_memory_alloc()
    disk_alloc = get_disk_alloc()
    schain_volume_alloc = get_schain_volume_alloc(disk_alloc)
    return {
        'cpu': cpu_alloc.dict(),
        'mem': mem_alloc.dict(),
        'disk': disk_alloc.dict(),
        'schain': {
            'storage_limit': get_storage_limit_alloc(),
            **schain_volume_alloc.volume_alloc
        }
    }


def get_schain_volume_alloc(disk_alloc: ResourceAlloc) -> SChainVolumeAlloc:
    proportions = get_schain_volume_proportions()
    return SChainVolumeAlloc(disk_alloc, proportions)


def get_schain_volume_proportions():
    return ALLOCATION_DATA['schain_volume_proportions']


def get_storage_limit_alloc(testnet=True):
    network = 'testnet' if testnet else 'mainnet'
    return ALLOCATION_DATA[network]['storage_limit']


def save_resource_allocation_config(exist_ok=False) -> bool:
    if os.path.isfile(RESOURCE_ALLOCATION_FILEPATH) and not exist_ok:
        msg = 'Resource allocation file is already exists'
        print(msg)
        logger.debug(msg)
        return True
    logger.info('Generating resource allocation file')
    try:
        resource_allocation_config = generate_resource_allocation_config()
        write_json(RESOURCE_ALLOCATION_FILEPATH, resource_allocation_config)
    except Exception as e:
        logger.exception(e)
        return False
    return True


def get_available_memory():
    memory = []
    for _ in range(0, TIMES):
        mem_info = psutil.virtual_memory()
        memory.append(mem_info.available)
        sleep(TIMEOUT)
    return sum(memory) / TIMES * MEMORY_FACTOR


def get_memory_alloc():
    available_memory = get_available_memory()
    return ResourceAlloc(available_memory)


def get_cpu_alloc():
    cpu_count = psutil.cpu_count()
    return ResourceAlloc(cpu_count, fractional=True)


def get_disk_alloc():
    disk_path = get_disk_path()
    try:
        disk_size = get_disk_size(disk_path)
    except subprocess.CalledProcessError:
        raise Exception("Couldn't get disk size, check disk mountpoint option.")
    # if check_is_partition(disk_path):
    #    raise Exception("You provided partition path instead of disk mountpoint.")
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
