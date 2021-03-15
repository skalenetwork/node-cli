import json
import os

import mock
import pytest

from node_cli.configs import ALLOCATION_FILEPATH
from node_cli.configs.resource_allocation import RESOURCE_ALLOCATION_FILEPATH
from node_cli.core.resources import (
    compose_resource_allocation_config,
    get_schain_volume_proportions,
    update_resource_allocation,
    get_static_disk_alloc,
    ResourceAlloc, SChainVolumeAlloc
)

from node_cli.utils.helper import write_json, safe_load_yml

SCHAIN_VOLUME_PARTS = {'test4': {'max_consensus_storage_bytes': 1, 'max_file_storage_bytes': 1, 'max_reserved_storage_bytes': 0, 'max_skaled_leveldb_storage_bytes': 1}, 'test': {'max_consensus_storage_bytes': 1, 'max_file_storage_bytes': 1, 'max_reserved_storage_bytes': 0, 'max_skaled_leveldb_storage_bytes': 1}, 'small': {'max_consensus_storage_bytes': 0, 'max_skaled_leveldb_storage_bytes': 0, 'max_file_storage_bytes': 0, 'max_reserved_storage_bytes': 0}, 'medium': {'max_consensus_storage_bytes': 1, 'max_file_storage_bytes': 1, 'max_reserved_storage_bytes': 0, 'max_skaled_leveldb_storage_bytes': 1}, 'large': {'max_consensus_storage_bytes': 38, 'max_skaled_leveldb_storage_bytes': 38, 'max_file_storage_bytes': 38, 'max_reserved_storage_bytes': 12}}  # noqa

DEFAULT_ENV_TYPE = 'devnet'

SMALL_DISK_SIZE = 10
NORMAL_DISK_SIZE = 80000000000
BIG_DISK_SIZE = NORMAL_DISK_SIZE * 100


def disk_alloc_mock(env_type):
    return ResourceAlloc(128)


INITIAL_CONFIG = {'test': 1}


@pytest.fixture
def resource_alloc_config():
    write_json(RESOURCE_ALLOCATION_FILEPATH, INITIAL_CONFIG)
    yield RESOURCE_ALLOCATION_FILEPATH
    os.remove(RESOURCE_ALLOCATION_FILEPATH)


def test_schain_resources_allocation():
    allocation_data = safe_load_yml(ALLOCATION_FILEPATH)
    proportions = get_schain_volume_proportions(allocation_data)
    res = ResourceAlloc(128)
    schain_volume_alloc = SChainVolumeAlloc(res, proportions)
    assert schain_volume_alloc.volume_alloc == SCHAIN_VOLUME_PARTS  # noqa


def test_generate_resource_allocation_config():
    with mock.patch('node_cli.core.resources.get_static_disk_alloc', new=disk_alloc_mock):
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

        assert resource_allocation_config['schain']['disk']['test4'] == 4
        assert resource_allocation_config['schain']['disk']['test'] == 4
        assert resource_allocation_config['schain']['disk']['small'] == 1
        assert resource_allocation_config['schain']['disk']['medium'] == 4
        assert resource_allocation_config['schain']['disk']['large'] == 128

        assert resource_allocation_config['ima']['cpu_shares'] == {'test4': 9, 'test': 9, 'small': 2, 'medium': 9, 'large': 307}  # noqa
        assert isinstance(resource_allocation_config['ima']['mem'], dict)

        assert resource_allocation_config['schain']['volume_limits'] == SCHAIN_VOLUME_PARTS
        assert resource_allocation_config['schain']['storage_limit'] == {
            'test4': 4294967296,
            'test': 4294967296,
            'small': 4294967296,
            'medium': 17179869184,
            'large': 549755813888
        }


def test_update_allocation_config(resource_alloc_config):
    with mock.patch('node_cli.core.resources.get_static_disk_alloc',
                    new=disk_alloc_mock):
        update_resource_allocation(DEFAULT_ENV_TYPE)
        with open(RESOURCE_ALLOCATION_FILEPATH) as jfile:
            assert json.load(jfile) != INITIAL_CONFIG


def test_get_static_disk_alloc_devnet(net_params_file):
    with mock.patch('node_cli.core.resources.get_disk_size', return_value=SMALL_DISK_SIZE):
        with pytest.raises(Exception):
            get_static_disk_alloc(DEFAULT_ENV_TYPE)

    with mock.patch('node_cli.core.resources.get_disk_size', return_value=NORMAL_DISK_SIZE):
        normal_static_disk_alloc = get_static_disk_alloc(DEFAULT_ENV_TYPE)

    with mock.patch('node_cli.core.resources.get_disk_size', return_value=BIG_DISK_SIZE):
        big_static_disk_alloc = get_static_disk_alloc(DEFAULT_ENV_TYPE)

    assert normal_static_disk_alloc.dict() == big_static_disk_alloc.dict()
    assert normal_static_disk_alloc.dict() == {
        'test4': 2374998016,
        'test': 2374998016,
        'small': 593749504,
        'medium': 2374998016,
        'large': 75999936512
    }


def test_get_static_disk_alloc_mainnet(net_params_file):
    env_type = 'mainnet'
    with mock.patch('node_cli.core.resources.get_disk_size', return_value=NORMAL_DISK_SIZE):
        with pytest.raises(Exception):
            get_static_disk_alloc(env_type)

    with mock.patch('node_cli.core.resources.get_disk_size', return_value=BIG_DISK_SIZE):
        big_static_disk_alloc = get_static_disk_alloc(env_type)

    assert big_static_disk_alloc.dict() == {
        'test4': 59374999552,
        'test': 59374999552,
        'small': 14843749888,
        'medium': 59374999552,
        'large': 1899999985664
    }
