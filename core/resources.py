import os
import logging
import psutil
import subprocess
from time import sleep

from tools.schain_types import SchainTypes
from tools.helper import write_json, read_json, run_cmd, format_output
from configs.resource_allocation import RESOURCE_ALLOCATION_FILEPATH, TIMES, TIMEOUT, \
    TINY_DIVIDER, SMALL_DIVIDER, MEDIUM_DIVIDER, MEMORY_FACTOR, DISK_FACTOR, DISK_MOUNTPOINT_FILEPATH

logger = logging.getLogger(__name__)


class ResourceAlloc():
    def __init__(self, value, fractional=False):
        self.values = {
            'part_test4': value / SMALL_DIVIDER,
            'part_test': value / SMALL_DIVIDER,
            'part_small': value / TINY_DIVIDER,
            'part_medium': value / SMALL_DIVIDER,
            'part_large': value / MEDIUM_DIVIDER
        }
        if not fractional:
            for k in self.values:
                self.values[k] = int(self.values[k])

    def dict(self):
        return self.values


def get_resource_allocation_info():
    return read_json(RESOURCE_ALLOCATION_FILEPATH)


def generate_resource_allocation_config():
    cpu_alloc = get_cpu_alloc()
    mem_alloc = get_memory_alloc()

    disk_path = get_disk_path()
    disk_alloc = get_disk_alloc(disk_path)
    return {
        'cpu': cpu_alloc.dict(),
        'mem': mem_alloc.dict(),
        'disk': disk_alloc.dict()
    }


def save_resource_allocation_config():
    if os.path.isfile(RESOURCE_ALLOCATION_FILEPATH):
        logger.debug('Resource allocation file is already exists')
        return
    logger.info('Generating resource allocation file')
    resource_allocation_config = generate_resource_allocation_config()
    write_json(RESOURCE_ALLOCATION_FILEPATH, resource_allocation_config)


def get_available_memory():
    memory = []
    for i in range(0, TIMES):
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


def get_disk_alloc(disk_path):
    try:
        disk_size = get_disk_size(disk_path)
    except subprocess.CalledProcessError:
        raise Exception("Couldn't get disk size, check disk mountpoint option.")
    #if check_is_partition(disk_path):
    #    raise Exception("You provided partition path instead of disk mountpoint.")
    free_space = disk_size * DISK_FACTOR
    return ResourceAlloc(free_space)


def get_disk_size(disk_path):
    disk_size_cmd = construct_disk_size_cmd(disk_path)
    res = run_cmd(disk_size_cmd, shell=True)
    stdout, stderr = format_output(res)
    return int(stdout)


def construct_disk_size_cmd(disk_path):
    return f'sudo blockdev --getsize64 {disk_path}'
    # return f'fdisk -l  {disk_path} | sed -n \'1p\' | grep -oP \', \K[^,]+\' | sed -n \'1p\'' # alternate version

def check_is_partition(disk_path):
    res = run_cmd(['blkid', disk_path])
    output = str(res.stdout)
    if 'PARTUUID' in output: return True
    return False

def get_allocation_option_name(schain):
    part_of_node = int(schain['partOfNode'])
    return SchainTypes(part_of_node).name

def get_disk_path():
    f = open(DISK_MOUNTPOINT_FILEPATH, "r")
    return f.read()