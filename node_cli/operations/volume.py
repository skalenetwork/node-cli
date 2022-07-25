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
import shutil
import tempfile

from node_cli.utils.helper import run_cmd
from node_cli.utils.git_utils import sync_repo
from node_cli.configs import (
    DOCKER_LVMPY_PATH,
    DOCKER_LVMPY_REPO_URL,
    FILESTORAGE_MAPPING,
    SCHAINS_MNT_DIR,
    SKALE_STATE_DIR
)

logger = logging.getLogger(__name__)


class FilesystemExistsError(Exception):
    pass


def update_docker_lvmpy_env(env):
    env['PHYSICAL_VOLUME'] = env['DISK_MOUNTPOINT']
    env['VOLUME_GROUP'] = 'schains'
    env['FILESTORAGE_MAPPING'] = FILESTORAGE_MAPPING
    env['SCHAINS_MNT_DIR'] = SCHAINS_MNT_DIR
    env['PATH'] = os.environ.get('PATH', None)
    return env


def ensure_filestorage_mapping(mapping_dir=FILESTORAGE_MAPPING):
    if not os.path.isdir(FILESTORAGE_MAPPING):
        os.makedirs(FILESTORAGE_MAPPING)


def sync_docker_lvmpy_repo(env):
    if os.path.isdir(DOCKER_LVMPY_PATH):
        shutil.rmtree(DOCKER_LVMPY_PATH)
    sync_repo(
        DOCKER_LVMPY_REPO_URL,
        DOCKER_LVMPY_PATH,
        env["DOCKER_LVMPY_STREAM"]
    )


def docker_lvmpy_update(env):
    sync_docker_lvmpy_repo(env)
    ensure_filestorage_mapping()
    logger.info('Running docker-lvmpy update script')
    update_docker_lvmpy_env(env)
    run_cmd(
        cmd=f'sudo -H -E {DOCKER_LVMPY_PATH}/scripts/update.sh'.split(),
        env=env
    )
    logger.info('docker-lvmpy update done')


def docker_lvmpy_install(env):
    sync_docker_lvmpy_repo(env)
    ensure_filestorage_mapping()
    update_docker_lvmpy_env(env)
    run_cmd(
        cmd=f'sudo -H -E {DOCKER_LVMPY_PATH}/scripts/install.sh'.split(),
        env=env
    )
    logger.info('docker-lvmpy installed')


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


def prepare_block_device(block_device):
    filesystem = get_block_device_filesystem(block_device)
    if filesystem == 'btrfs':
        logger.info('%s already formatted as btrfs', block_device)
        ensure_btrfs_for_all_space(block_device)
    else:
        logger.info('%s contains %s filesystem', block_device, filesystem)
        format_as_btrfs(block_device)
    mountpoint = os.path.join(SKALE_STATE_DIR, 'schains')
    mount_device(block_device, mountpoint)


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
