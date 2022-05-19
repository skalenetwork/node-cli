import os

import pytest

from node_cli.core.host import (
    is_btrfs_module_autoloaded,
    ensure_btrfs_kernel_module_autoloaded
)


@pytest.fixture
def tmp_path(tmp_dir_path):
    path = os.path.join(tmp_dir_path, 'modules')
    return path


def test_btrfs_module_autoload_config(tmp_path):
    ensure_btrfs_kernel_module_autoloaded(tmp_path)
    assert is_btrfs_module_autoloaded(tmp_path)

    with open(tmp_path, 'w') as tmp_file:
        tmp_file.write('')

    assert not is_btrfs_module_autoloaded(tmp_path)

    with open(tmp_path, 'w') as tmp_file:
        tmp_file.write('# btrfs')

    assert not is_btrfs_module_autoloaded(tmp_path)


def test_is_btrfs_module_autoloaded_negative(tmp_path):
    assert not is_btrfs_module_autoloaded(tmp_path)
    with open(tmp_path, 'w') as tmp_file:
        tmp_file.write('')

    assert not is_btrfs_module_autoloaded(tmp_path)

    with open(tmp_path, 'w') as tmp_file:
        tmp_file.write('# btrfs')

    assert not is_btrfs_module_autoloaded(tmp_path)
