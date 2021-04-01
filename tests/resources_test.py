import json
import os

import mock
import pytest

from configs import ALLOCATION_FILEPATH, CONFIGS_FILEPATH
from configs.resource_allocation import RESOURCE_ALLOCATION_FILEPATH
from core.resources import (
    compose_resource_allocation_config,
    update_resource_allocation,
    ResourceAlloc, get_cpu_alloc, get_memory_alloc,
    compose_storage_limit, verify_disk_size
)

from core.helper import safe_load_yml
from tools.helper import write_json

SCHAIN_VOLUME_PARTS = {'large': {'max_consensus_storage_bytes': 22799980953, 'max_file_storage_bytes': 22799980953, 'max_reserved_storage_bytes': 7599993651, 'max_skaled_leveldb_storage_bytes': 22799980953}, 'medium': {'max_consensus_storage_bytes': 712499404, 'max_file_storage_bytes': 712499404, 'max_reserved_storage_bytes': 237499801, 'max_skaled_leveldb_storage_bytes': 712499404}, 'small': {'max_consensus_storage_bytes': 178124851, 'max_file_storage_bytes': 178124851, 'max_reserved_storage_bytes': 59374950, 'max_skaled_leveldb_storage_bytes': 178124851}, 'test': {'max_consensus_storage_bytes': 712499404, 'max_file_storage_bytes': 712499404, 'max_reserved_storage_bytes': 237499801, 'max_skaled_leveldb_storage_bytes': 712499404}, 'test4': {'max_consensus_storage_bytes': 712499404, 'max_file_storage_bytes': 712499404, 'max_reserved_storage_bytes': 237499801, 'max_skaled_leveldb_storage_bytes': 712499404}}  # noqa

DEFAULT_ENV_TYPE = 'devnet'

SMALL_DISK_SIZE = 10
NORMAL_DISK_SIZE = 80000000000
BIG_DISK_SIZE = NORMAL_DISK_SIZE * 100

TEST_MEMORY = 10000000


def disk_alloc_mock(env_type):
    return ResourceAlloc(128)


INITIAL_CONFIG = {'test': 1}


@pytest.fixture
def net_configs():
    return safe_load_yml(CONFIGS_FILEPATH)


@pytest.fixture
def schain_allocation_data():
    return safe_load_yml(ALLOCATION_FILEPATH)


@pytest.fixture
def resource_alloc_config():
    write_json(RESOURCE_ALLOCATION_FILEPATH, INITIAL_CONFIG)
    yield RESOURCE_ALLOCATION_FILEPATH
    os.remove(RESOURCE_ALLOCATION_FILEPATH)


def test_generate_resource_allocation_config():
    with mock.patch('core.resources.get_disk_size', return_value=NORMAL_DISK_SIZE):
        resource_allocation_config = compose_resource_allocation_config(DEFAULT_ENV_TYPE)

        assert resource_allocation_config['schain']['cpu_shares']['test4'] == 22
        assert resource_allocation_config['schain']['cpu_shares']['test'] == 22
        assert resource_allocation_config['schain']['cpu_shares']['small'] == 5
        assert resource_allocation_config['schain']['cpu_shares']['medium'] == 22
        assert resource_allocation_config['schain']['cpu_shares']['large'] == 716

        assert isinstance(resource_allocation_config['schain']['mem']['test4'], int)
        assert isinstance(resource_allocation_config['schain']['mem']['test'], int)
        assert isinstance(resource_allocation_config['schain']['mem']['small'], int)
        assert isinstance(resource_allocation_config['schain']['mem']['medium'], int)
        assert isinstance(resource_allocation_config['schain']['mem']['large'], int)

        assert resource_allocation_config['schain']['disk']['test4'] == 2374998016
        assert resource_allocation_config['schain']['disk']['test'] == 2374998016
        assert resource_allocation_config['schain']['disk']['small'] == 593749504
        assert resource_allocation_config['schain']['disk']['medium'] == 2374998016
        assert resource_allocation_config['schain']['disk']['large'] == 75999936512

        assert resource_allocation_config['ima']['cpu_shares'] == {'test4': 9, 'test': 9, 'small': 2, 'medium': 9, 'large': 307}  # noqa
        assert isinstance(resource_allocation_config['ima']['mem'], dict)

        print(resource_allocation_config['schain']['volume_limits'])
        assert resource_allocation_config['schain']['volume_limits'] == SCHAIN_VOLUME_PARTS
        assert resource_allocation_config['schain']['storage_limit'] == {
            'test4': 427499642,
            'test': 427499642,
            'small': 106874910,
            'medium': 427499642,
            'large': 13679988571
        }


def test_update_allocation_config(resource_alloc_config):
    with mock.patch('core.resources.get_disk_size', return_value=BIG_DISK_SIZE):
        update_resource_allocation(DEFAULT_ENV_TYPE)
        with open(RESOURCE_ALLOCATION_FILEPATH) as jfile:
            assert json.load(jfile) != INITIAL_CONFIG


def test_get_static_disk_alloc_devnet(net_configs, schain_allocation_data):
    with mock.patch('core.resources.get_disk_size', return_value=SMALL_DISK_SIZE):
        with pytest.raises(Exception):
            verify_disk_size(net_configs, DEFAULT_ENV_TYPE)

    with mock.patch('core.resources.get_disk_size', return_value=NORMAL_DISK_SIZE):
        verify_disk_size(net_configs, DEFAULT_ENV_TYPE)

    with mock.patch('core.resources.get_disk_size', return_value=BIG_DISK_SIZE):
        verify_disk_size(net_configs, DEFAULT_ENV_TYPE)

    assert schain_allocation_data[DEFAULT_ENV_TYPE]['disk'] == {
        'test4': 2374998016,
        'test': 2374998016,
        'small': 593749504,
        'medium': 2374998016,
        'large': 75999936512
    }


def test_get_static_disk_alloc_mainnet(net_configs):
    env_type = 'mainnet'

    with mock.patch('core.resources.get_disk_size', return_value=NORMAL_DISK_SIZE):
        with pytest.raises(Exception):
            verify_disk_size(net_configs, env_type)

    with mock.patch('core.resources.get_disk_size', return_value=BIG_DISK_SIZE):
        verify_disk_size(net_configs, env_type)


def test_get_cpu_alloc():
    net_configs = safe_load_yml(CONFIGS_FILEPATH)
    schain_cpu_alloc, ima_cpu_alloc = get_cpu_alloc(net_configs)
    schain_cpu_alloc_dict = schain_cpu_alloc.dict()
    ima_cpu_alloc_dict = ima_cpu_alloc.dict()

    assert schain_cpu_alloc_dict['test4'] == 22
    assert schain_cpu_alloc_dict['test'] == 22
    assert schain_cpu_alloc_dict['small'] == 5
    assert schain_cpu_alloc_dict['medium'] == 22
    assert schain_cpu_alloc_dict['large'] == 716

    assert ima_cpu_alloc_dict['test4'] == 9
    assert ima_cpu_alloc_dict['test'] == 9
    assert ima_cpu_alloc_dict['small'] == 2
    assert ima_cpu_alloc_dict['medium'] == 9
    assert ima_cpu_alloc_dict['large'] == 307


def test_get_memory_alloc():
    net_configs = safe_load_yml(CONFIGS_FILEPATH)
    with mock.patch('core.resources.get_total_memory', return_value=TEST_MEMORY):
        schain_mem_alloc, ima_mem_alloc = get_memory_alloc(net_configs)
    schain_mem_alloc_dict = schain_mem_alloc.dict()
    ima_mem_alloc_dict = ima_mem_alloc.dict()

    assert schain_mem_alloc_dict['test4'] == 218750
    assert schain_mem_alloc_dict['test'] == 218750
    assert schain_mem_alloc_dict['small'] == 54687
    assert schain_mem_alloc_dict['medium'] == 218750
    assert schain_mem_alloc_dict['large'] == 7000000

    assert ima_mem_alloc_dict['test4'] == 93750
    assert ima_mem_alloc_dict['test'] == 93750
    assert ima_mem_alloc_dict['small'] == 23437
    assert ima_mem_alloc_dict['medium'] == 93750
    assert ima_mem_alloc_dict['large'] == 3000000


def test_compose_storage_limit():
    schain_allocation_data = safe_load_yml(ALLOCATION_FILEPATH)
    storage_limit = compose_storage_limit(schain_allocation_data['mainnet']['leveldb'])
    assert storage_limit == {
        'large': 341999997419,
        'medium': 10687499919,
        'small': 2671874979,
        'test': 10687499919,
        'test4': 10687499919
    }
