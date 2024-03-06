import json
import os

import mock
import pytest

from node_cli.configs import ALLOCATION_FILEPATH, STATIC_PARAMS_FILEPATH
from node_cli.configs.resource_allocation import RESOURCE_ALLOCATION_FILEPATH
from node_cli.core.resources import (
    compose_resource_allocation_config,
    update_resource_allocation,
    get_cpu_alloc, get_memory_alloc, verify_disk_size
)

from node_cli.utils.helper import write_json, safe_load_yml

SCHAIN_VOLUME_PARTS = {'large': {'max_consensus_storage_bytes': 21311992627, 'max_file_storage_bytes': 21311992627, 'max_reserved_storage_bytes': 7103997542, 'max_skaled_leveldb_storage_bytes': 21311992627}, 'medium': {'max_consensus_storage_bytes': 2663999078, 'max_file_storage_bytes': 2663999078, 'max_reserved_storage_bytes': 887999692, 'max_skaled_leveldb_storage_bytes': 2663999078}, 'small': {'max_consensus_storage_bytes': 166499942, 'max_file_storage_bytes': 166499942, 'max_reserved_storage_bytes': 55499980, 'max_skaled_leveldb_storage_bytes': 166499942}, 'test': {'max_consensus_storage_bytes': 2663999078, 'max_file_storage_bytes': 2663999078, 'max_reserved_storage_bytes': 887999692, 'max_skaled_leveldb_storage_bytes': 2663999078}, 'test4': {'max_consensus_storage_bytes': 2663999078, 'max_file_storage_bytes': 2663999078, 'max_reserved_storage_bytes': 887999692, 'max_skaled_leveldb_storage_bytes': 2663999078}}  # noqa

DEFAULT_ENV_TYPE = 'devnet'

SMALL_DISK_SIZE = 10
NORMAL_DISK_SIZE = 80000000000
BIG_DISK_SIZE = NORMAL_DISK_SIZE * 100

TEST_MEMORY = 10000000

INITIAL_CONFIG = {'test': 1}


@pytest.fixture
def params_by_env_type():
    return safe_load_yml(STATIC_PARAMS_FILEPATH)


@pytest.fixture
def schain_allocation_data():
    return safe_load_yml(ALLOCATION_FILEPATH)


@pytest.fixture
def resource_alloc_config():
    write_json(RESOURCE_ALLOCATION_FILEPATH, INITIAL_CONFIG)
    yield RESOURCE_ALLOCATION_FILEPATH
    os.remove(RESOURCE_ALLOCATION_FILEPATH)


def test_generate_resource_allocation_config():
    with mock.patch('node_cli.core.resources.get_disk_size', return_value=NORMAL_DISK_SIZE):
        resource_allocation_config = compose_resource_allocation_config(DEFAULT_ENV_TYPE)

        assert resource_allocation_config['schain']['cpu_shares']['test4'] == 102
        assert resource_allocation_config['schain']['cpu_shares']['test'] == 102
        assert resource_allocation_config['schain']['cpu_shares']['small'] == 6
        assert resource_allocation_config['schain']['cpu_shares']['medium'] == 102
        assert resource_allocation_config['schain']['cpu_shares']['large'] == 819

        assert isinstance(resource_allocation_config['schain']['mem']['test4'], int)
        assert isinstance(resource_allocation_config['schain']['mem']['test'], int)
        assert isinstance(resource_allocation_config['schain']['mem']['small'], int)
        assert isinstance(resource_allocation_config['schain']['mem']['medium'], int)
        assert isinstance(resource_allocation_config['schain']['mem']['large'], int)

        assert resource_allocation_config['schain']['disk']['test4'] == 8879996928
        assert resource_allocation_config['schain']['disk']['test'] == 8879996928
        assert resource_allocation_config['schain']['disk']['small'] == 554999808
        assert resource_allocation_config['schain']['disk']['medium'] == 8879996928
        assert resource_allocation_config['schain']['disk']['large'] == 71039975424

        assert resource_allocation_config['ima']['cpu_shares'] == {
            'large': 204, 'medium': 25, 'small': 1, 'test': 25, 'test4': 25}
        assert isinstance(resource_allocation_config['ima']['mem'], dict)

        assert resource_allocation_config['schain']['volume_limits'] == SCHAIN_VOLUME_PARTS


def test_update_allocation_config(resource_alloc_config):
    with mock.patch('node_cli.core.resources.get_disk_size', return_value=BIG_DISK_SIZE):
        update_resource_allocation(DEFAULT_ENV_TYPE)
        with open(RESOURCE_ALLOCATION_FILEPATH) as jfile:
            assert json.load(jfile) != INITIAL_CONFIG


def test_get_static_disk_alloc_devnet(
    params_by_env_type,
    schain_allocation_data
):
    env_configs = params_by_env_type['envs']['devnet']
    block_device = '/dev/test'
    with mock.patch('node_cli.core.resources.get_disk_size', return_value=SMALL_DISK_SIZE):
        with pytest.raises(Exception):
            verify_disk_size(block_device, env_configs)

    with mock.patch('node_cli.core.resources.get_disk_size', return_value=NORMAL_DISK_SIZE):
        verify_disk_size(block_device, env_configs)

    with mock.patch('node_cli.core.resources.get_disk_size', return_value=BIG_DISK_SIZE):
        verify_disk_size(block_device, env_configs)

    assert schain_allocation_data[DEFAULT_ENV_TYPE]['disk'] == {
        'large': 71039975424,
        'medium': 8879996928,
        'small': 554999808,
        'test': 8879996928,
        'test4': 8879996928
    }


def test_get_static_disk_alloc_mainnet(params_by_env_type):
    env_configs = params_by_env_type['envs']['mainnet']
    block_device = '/dev/test'

    with mock.patch('node_cli.core.resources.get_disk_size', return_value=NORMAL_DISK_SIZE):
        with pytest.raises(Exception):
            verify_disk_size(block_device, env_configs)

    with mock.patch('node_cli.core.resources.get_disk_size', return_value=BIG_DISK_SIZE):
        verify_disk_size(block_device, env_configs)


def test_get_cpu_alloc(params_by_env_type):
    common_config = params_by_env_type['common']
    schain_cpu_alloc, ima_cpu_alloc = get_cpu_alloc(common_config)
    schain_cpu_alloc_dict = schain_cpu_alloc.dict()
    ima_cpu_alloc_dict = ima_cpu_alloc.dict()

    assert schain_cpu_alloc_dict['test4'] == 102
    assert schain_cpu_alloc_dict['test'] == 102
    assert schain_cpu_alloc_dict['small'] == 6
    assert schain_cpu_alloc_dict['medium'] == 102
    assert schain_cpu_alloc_dict['large'] == 819

    assert ima_cpu_alloc_dict['test4'] == 25
    assert ima_cpu_alloc_dict['test'] == 25
    assert ima_cpu_alloc_dict['small'] == 1
    assert ima_cpu_alloc_dict['medium'] == 25
    assert ima_cpu_alloc_dict['large'] == 204


def test_get_memory_alloc(params_by_env_type):
    common_config = params_by_env_type['common']
    with mock.patch('node_cli.core.resources.get_total_memory', return_value=TEST_MEMORY):
        schain_mem_alloc, ima_mem_alloc = get_memory_alloc(common_config)
    schain_mem_alloc_dict = schain_mem_alloc.dict()
    ima_mem_alloc_dict = ima_mem_alloc.dict()

    assert schain_mem_alloc_dict['test4'] == 1000000
    assert schain_mem_alloc_dict['test'] == 1000000
    assert schain_mem_alloc_dict['small'] == 62500
    assert schain_mem_alloc_dict['medium'] == 1000000
    assert schain_mem_alloc_dict['large'] == 8000000

    assert ima_mem_alloc_dict['test4'] == 250000
    assert ima_mem_alloc_dict['test'] == 250000
    assert ima_mem_alloc_dict['small'] == 15625
    assert ima_mem_alloc_dict['medium'] == 250000
    assert ima_mem_alloc_dict['large'] == 2000000


def test_leveldb_limits():
    with mock.patch('node_cli.core.resources.get_disk_size', return_value=NORMAL_DISK_SIZE):
        resource_allocation_config = compose_resource_allocation_config(DEFAULT_ENV_TYPE)
    assert resource_allocation_config['schain']['leveldb_limits'] == {
        'large': {'contract_storage': 12787195576, 'db_storage': 4262398525},
        'medium': {'contract_storage': 1598399446, 'db_storage': 532799815},
        'small': {'contract_storage': 99899965, 'db_storage': 33299988},
        'test': {'contract_storage': 1598399446, 'db_storage': 532799815},
        'test4': {'contract_storage': 1598399446, 'db_storage': 532799815}
    }
