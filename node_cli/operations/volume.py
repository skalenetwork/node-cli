#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
#
#   Copyright (C) 2021 SKALE Labs
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

import glob
import logging
import os
import tempfile

from node_cli.utils.helper import run_cmd
from node_cli.configs import (
    FILESTORAGE_MAPPING,
    SCHAINS_MNT_DIR_SINGLE_CHAIN,
    SKALE_STATE_DIR,
)

logger = logging.getLogger(__name__)


def ensure_filestorage_mapping():
    os.makedirs(FILESTORAGE_MAPPING, exist_ok=True)


def block_device_mounted(block_device):
    with open('/proc/mounts') as mounts:
        return any(block_device in mount for mount in mounts.readlines())


def ensure_not_mounted(block_device):
    logger.info('Making sure %s is not mounted', block_device)
    if block_device_mounted(block_device):
        run_cmd(['umount', block_device])


def cleanup_static_path(filestorage_mapping=FILESTORAGE_MAPPING):
    logger.info('Removing all links from filestorage mapping')
    for dir_link in glob.glob(os.path.join(filestorage_mapping, '*')):
        logger.debug('Unlinking %s', dir_link)
        if os.path.islink(dir_link):
            os.unlink(dir_link)


def cleanup_volume_artifacts(block_device):
    ensure_not_mounted(block_device)
    cleanup_static_path()


def get_block_device_filesystem(block_device):
    r = run_cmd(['blkid', '-o', 'udev', block_device])
    output = r.stdout.decode('utf-8')
    logger.debug('blkid output %s', output)
    fs_line = next(filter(lambda s: s.startswith('ID_FS_TYPE'), output.split('\n')))
    return fs_line.split('=')[1]


def format_as_btrfs(block_device):
    logger.info('Formating %s as btrfs', block_device)
    run_cmd(['mkfs.btrfs', block_device, '-f'])


def mount_device(block_device, mountpoint):
    os.makedirs(mountpoint, exist_ok=True)
    logger.info('Mounting %s device', block_device)
    run_cmd(['mount', block_device, mountpoint])


def prepare_block_device(block_device, force=False):
    filesystem = None
    try:
        filesystem = get_block_device_filesystem(block_device)
    except Exception as e:
        logger.info('Cannot get filesystem type %s', e)
        logger.debug('Cannot get filesystem type', exc_info=True)
        if not force:
            raise

    if filesystem == 'btrfs':
        logger.info('%s already formatted as btrfs', block_device)
        ensure_btrfs_for_all_space(block_device)
    else:
        logger.info('%s contains %s filesystem', block_device, filesystem)
        format_as_btrfs(block_device)
    mount_device(block_device, SCHAINS_MNT_DIR_SINGLE_CHAIN)


def max_resize_btrfs(path):
    run_cmd(['btrfs', 'filesystem', 'resize', 'max', path])


def ensure_btrfs_for_all_space(block_device):
    with tempfile.TemporaryDirectory(dir=SKALE_STATE_DIR) as mountpoint:
        try:
            mount_device(block_device, mountpoint)
            logger.info('Resizing btrfs filesystem for %s', block_device)
            max_resize_btrfs(mountpoint)
        finally:
            ensure_not_mounted(block_device)
