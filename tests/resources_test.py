import mock
from core.resources import (generate_resource_allocation_config, get_schain_volume_proportions,
                            ResourceAlloc, SChainVolumeAlloc)


SCHAIN_VOLUME_PARTS = {'part_test4': {'maxConsensusStorageBytes': 4, 'maxSkaledLeveldbStorageBytes': 4, 'maxFileStorageBytes': 4, 'maxReservedStorageBytes': 1}, 'part_test': {'maxConsensusStorageBytes': 4, 'maxSkaledLeveldbStorageBytes': 4, 'maxFileStorageBytes': 4, 'maxReservedStorageBytes': 1}, 'part_small': {'maxConsensusStorageBytes': 0, 'maxSkaledLeveldbStorageBytes': 0, 'maxFileStorageBytes': 0, 'maxReservedStorageBytes': 0}, 'part_medium': {'maxConsensusStorageBytes': 4, 'maxSkaledLeveldbStorageBytes': 4, 'maxFileStorageBytes': 4, 'maxReservedStorageBytes': 1}, 'part_large': {'maxConsensusStorageBytes': 38, 'maxSkaledLeveldbStorageBytes': 38, 'maxFileStorageBytes': 38, 'maxReservedStorageBytes': 12}}  # noqa


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

        assert resource_allocation_config.get('cpu', None)
        assert resource_allocation_config.get('mem', None)
        assert resource_allocation_config.get('disk', None)

        assert resource_allocation_config['disk']['part_test4'] == 16
        assert resource_allocation_config['disk']['part_test'] == 16
        assert resource_allocation_config['disk']['part_small'] == 1
        assert resource_allocation_config['disk']['part_medium'] == 16
        assert resource_allocation_config['disk']['part_large'] == 128

        assert resource_allocation_config['schain'] == {
            'storage_limit': {
                'test4': 655360000,
                'test': 655360000,
                'tiny': 655360000,
                'small': 10737418240,
                'medium': 85899345920
            },
            **SCHAIN_VOLUME_PARTS
        }
