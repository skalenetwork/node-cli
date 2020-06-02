import mock
from core.resources import generate_resource_allocation_config, ResourceAlloc


def disk_alloc_mock():
    return ResourceAlloc(100)


def test_generate_resource_allocation_config():
    with mock.patch('core.resources.get_disk_alloc',
                    new=disk_alloc_mock):
        resource_allocation_config = generate_resource_allocation_config()
        print(resource_allocation_config)

        assert resource_allocation_config.get('cpu', None)
        assert resource_allocation_config.get('mem', None)
        assert resource_allocation_config.get('disk', None)

        assert resource_allocation_config['disk']['part_test4'] == 12
        assert resource_allocation_config['disk']['part_test'] == 12
        assert resource_allocation_config['disk']['part_small'] == 0
        assert resource_allocation_config['disk']['part_medium'] == 12
        assert resource_allocation_config['disk']['part_large'] == 100

        assert resource_allocation_config['schain'] == {
            'storage_limit': {
                'storage_limit': {
                    'test4': 655360000,
                    'test': 655360000,
                    'tiny': 655360000,
                    'small': 10737418240,
                    'medium': 85899345920
                }
            }
        }
