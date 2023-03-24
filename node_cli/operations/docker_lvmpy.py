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

import crontab

from node_cli.utils.git_utils import sync_repo
from node_cli.configs import (
    DOCKER_LVMPY_PATH,
    DOCKER_LVMPY_REPO_URL,
    FILESTORAGE_MAPPING,
    LVMPY_RUN_CMD,
    LVMPY_HEAL_CMD,
    LVMPY_CRON_LOG_PATH,
    LVMPY_CRON_SCHEDULE_MINUTES,
    SCHAINS_MNT_DIR,
    VOLUME_GROUP
)
from lvmpy.src.install import setup as setup_lvmpy

logger = logging.getLogger(__name__)


def update_docker_lvmpy_env(env):
    env['PHYSICAL_VOLUME'] = env['DISK_MOUNTPOINT']
    env['VOLUME_GROUP'] = 'schains'
    env['FILESTORAGE_MAPPING'] = FILESTORAGE_MAPPING
    env['MNT_DIR'] = SCHAINS_MNT_DIR
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


def lvmpy_install(env):
    ensure_filestorage_mapping()
    logging.info('Configuring and starting lvmpy')
    setup_lvmpy(
        block_device=env['DISK_MOUNTPOINT'],
        volume_group=VOLUME_GROUP,
        exec_start=LVMPY_RUN_CMD
    )
    init_healing_cron()
    logger.info('docker-lvmpy is configured and started')


def init_healing_cron():
    logger.info('Configuring cron job for healing lvmpy')
    cron_line = f'{LVMPY_HEAL_CMD} >> {LVMPY_CRON_LOG_PATH} 2>&1'
    legacy_line = f'cd /opt/docker-lvmpy && venv/bin/python -c "import health; health.heal_service()" >> {LVMPY_CRON_LOG_PATH} 2>&1'  # noqa

    with crontab.CronTab(user='root') as c:
        jobs = [c.command for c in c]
        if legacy_line in jobs:
            c.remove_all(command=legacy_line)
        if cron_line not in jobs:
            job = c.new(
                command=cron_line
            )
            job.minute.every(LVMPY_CRON_SCHEDULE_MINUTES)
