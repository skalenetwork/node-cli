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


def get_block_device_filesystem(block_device):
    with tempfile.TemporaryDirectory(dir=SKALE_STATE_DIR) as tempdir:
        try:
            run_cmd(['mount', block_device, tempdir.path])
            r = run_cmd(['stat', '-f', '-c', '%T'])
            return r.stdout.decode('utf-8')
        finally:
            run_cmd(['umount', block_device])


def format_as_btrfs(block_device):
    filesystem = get_block_device_filesystem(block_device)
    logger.info('Found filesystem on the %s: %s', block_device, filesystem)
    if filesystem == 'btrfs':
        logger.info('Formatting %s as btrfs', block_device)
        run_cmd(['mkfs.btrfs', block_device])
    else:
        raise FilesystemExistsError(f'{block_device} contains {filesystem}')


def mount_device(block_device, mountpoint):
    os.makedirs(mountpoint, exists_ok=True)
    logger.info('Mounting %s as btrfs', block_device)
    run_cmd(['mount', block_device, mountpoint])


def prepare_block_device(block_device):
    mountpoint = os.path.join(SKALE_STATE_DIR, 'schains')
    if not os.path.ismount(mountpoint):
        format_as_btrfs(block_device)
        mount_device(block_device, mountpoint)
