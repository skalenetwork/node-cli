import json
import os

import mock
import pytest

from node_cli.configs import ALLOCATION_FILEPATH, ENVIRONMENT_PARAMS_FILEPATH
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
def env_configs():
    return safe_load_yml(ENVIRONMENT_PARAMS_FILEPATH)


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

        assert resource_allocation_config['schain']['cpu_shares']['test4'] == 89
        assert resource_allocation_config['schain']['cpu_shares']['test'] == 89
        assert resource_allocation_config['schain']['cpu_shares']['small'] == 5
        assert resource_allocation_config['schain']['cpu_shares']['medium'] == 89
        assert resource_allocation_config['schain']['cpu_shares']['large'] == 716

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

        assert resource_allocation_config['ima']['cpu_shares'] == {'large': 307, 'medium': 38, 'small': 2, 'test': 38, 'test4': 38}  # noqa
        assert isinstance(resource_allocation_config['ima']['mem'], dict)

        assert resource_allocation_config['schain']['volume_limits'] == SCHAIN_VOLUME_PARTS


def test_update_allocation_config(resource_alloc_config):
    with mock.patch('node_cli.core.resources.get_disk_size', return_value=BIG_DISK_SIZE):
        update_resource_allocation(DEFAULT_ENV_TYPE)
        with open(RESOURCE_ALLOCATION_FILEPATH) as jfile:
            assert json.load(jfile) != INITIAL_CONFIG


def test_get_static_disk_alloc_devnet(env_configs, schain_allocation_data):
    with mock.patch('node_cli.core.resources.get_disk_size', return_value=SMALL_DISK_SIZE):
        with pytest.raises(Exception):
            verify_disk_size(env_configs, DEFAULT_ENV_TYPE)

    with mock.patch('node_cli.core.resources.get_disk_size', return_value=NORMAL_DISK_SIZE):
        verify_disk_size(env_configs, DEFAULT_ENV_TYPE)

    with mock.patch('node_cli.core.resources.get_disk_size', return_value=BIG_DISK_SIZE):
        verify_disk_size(env_configs, DEFAULT_ENV_TYPE)

    assert schain_allocation_data[DEFAULT_ENV_TYPE]['disk'] == {
        'large': 71039975424,
        'medium': 8879996928,
        'small': 554999808,
        'test': 8879996928,
        'test4': 8879996928
    }


def test_get_static_disk_alloc_mainnet(env_configs):
    env_type = 'mainnet'

    with mock.patch('node_cli.core.resources.get_disk_size', return_value=NORMAL_DISK_SIZE):
        with pytest.raises(Exception):
            verify_disk_size(env_configs, env_type)

    with mock.patch('node_cli.core.resources.get_disk_size', return_value=BIG_DISK_SIZE):
        verify_disk_size(env_configs, env_type)


def test_get_cpu_alloc():
    env_configs = safe_load_yml(ENVIRONMENT_PARAMS_FILEPATH)
    schain_cpu_alloc, ima_cpu_alloc = get_cpu_alloc(env_configs)
    schain_cpu_alloc_dict = schain_cpu_alloc.dict()
    ima_cpu_alloc_dict = ima_cpu_alloc.dict()

    assert schain_cpu_alloc_dict['test4'] == 89
    assert schain_cpu_alloc_dict['test'] == 89
    assert schain_cpu_alloc_dict['small'] == 5
    assert schain_cpu_alloc_dict['medium'] == 89
    assert schain_cpu_alloc_dict['large'] == 716

    assert ima_cpu_alloc_dict['test4'] == 38
    assert ima_cpu_alloc_dict['test'] == 38
    assert ima_cpu_alloc_dict['small'] == 2
    assert ima_cpu_alloc_dict['medium'] == 38
    assert ima_cpu_alloc_dict['large'] == 307


def test_get_memory_alloc():
    env_configs = safe_load_yml(ENVIRONMENT_PARAMS_FILEPATH)
    with mock.patch('node_cli.core.resources.get_total_memory', return_value=TEST_MEMORY):
        schain_mem_alloc, ima_mem_alloc = get_memory_alloc(env_configs)
    schain_mem_alloc_dict = schain_mem_alloc.dict()
    ima_mem_alloc_dict = ima_mem_alloc.dict()

    assert schain_mem_alloc_dict['test4'] == 875000
    assert schain_mem_alloc_dict['test'] == 875000
    assert schain_mem_alloc_dict['small'] == 54687
    assert schain_mem_alloc_dict['medium'] == 875000
    assert schain_mem_alloc_dict['large'] == 7000000

    assert ima_mem_alloc_dict['test4'] == 375000
    assert ima_mem_alloc_dict['test'] == 375000
    assert ima_mem_alloc_dict['small'] == 23437
    assert ima_mem_alloc_dict['medium'] == 375000
    assert ima_mem_alloc_dict['large'] == 3000000


def test_leveldb_limits():
    with mock.patch('node_cli.core.resources.get_disk_size', return_value=NORMAL_DISK_SIZE):
        resource_allocation_config = compose_resource_allocation_config(DEFAULT_ENV_TYPE)

    assert resource_allocation_config['schain']['leveldb_limits'] == {
        'large': {'contract_storage': 12787195576, 'db_storage': 8524797050},
        'medium': {'contract_storage': 1598399446, 'db_storage': 1065599631},
        'small': {'contract_storage': 99899965, 'db_storage': 66599976},
        'test': {'contract_storage': 1598399446, 'db_storage': 1065599631},
        'test4': {'contract_storage': 1598399446, 'db_storage': 1065599631}
    }
