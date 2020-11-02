import mock
from core.resources import (generate_resource_allocation_config, get_schain_volume_proportions,
                            ResourceAlloc, SChainVolumeAlloc)


SCHAIN_VOLUME_PARTS = {'test4': {'max_consensus_storage_bytes': 4, 'max_skaled_leveldb_storage_bytes': 4, 'max_file_storage_bytes': 4, 'max_reserved_storage_bytes': 1}, 'test': {'max_consensus_storage_bytes': 4, 'max_skaled_leveldb_storage_bytes': 4, 'max_file_storage_bytes': 4, 'max_reserved_storage_bytes': 1}, 'small': {'max_consensus_storage_bytes': 0, 'max_skaled_leveldb_storage_bytes': 0, 'max_file_storage_bytes': 0, 'max_reserved_storage_bytes': 0}, 'medium': {'max_consensus_storage_bytes': 4, 'max_skaled_leveldb_storage_bytes': 4, 'max_file_storage_bytes': 4, 'max_reserved_storage_bytes': 1}, 'large': {'max_consensus_storage_bytes': 38, 'max_skaled_leveldb_storage_bytes': 38, 'max_file_storage_bytes': 38, 'max_reserved_storage_bytes': 12}}  # noqa


def disk_alloc_mock():
    return ResourceAlloc(128)


def test_schain_resources_allocation():
    proportions = get_schain_volume_proportions()
    res = ResourceAlloc(128)
    schain_volume_alloc = SChainVolumeAlloc(res, proportions)
    assert schain_volume_alloc.volume_alloc == SCHAIN_VOLUME_PARTS  # noqa


def test_generate_resource_allocation_config():
    with mock.patch('core.resources.get_disk_alloc',
                    new=disk_alloc_mock):
        resource_allocation_config = generate_resource_allocation_config()

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

        assert resource_allocation_config['schain']['disk']['test4'] == 16
        assert resource_allocation_config['schain']['disk']['test'] == 16
        assert resource_allocation_config['schain']['disk']['small'] == 1
        assert resource_allocation_config['schain']['disk']['medium'] == 16
        assert resource_allocation_config['schain']['disk']['large'] == 128

        assert resource_allocation_config['ima']['cpu_shares'] == {'test4': 38, 'test': 38, 'small': 2, 'medium': 38, 'large': 307} # noqa
        assert isinstance(resource_allocation_config['ima']['mem'], dict)

        assert resource_allocation_config['schain']['volume_limits'] == SCHAIN_VOLUME_PARTS
        assert resource_allocation_config['schain']['storage_limit'] == {
            'test4': 655360000,
            'test': 655360000,
            'small': 655360000,
            'medium': 10737418240,
            'large': 85899345920
        }
