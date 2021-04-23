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

import os
import shlex
import shutil
import datetime

from node_cli.core.host import safe_mk_dirs
from node_cli.utils.helper import run_cmd
from node_cli.utils.docker_utils import (
    save_container_logs, get_containers
)
from node_cli.configs import REMOVED_CONTAINERS_FOLDER_PATH
from node_cli.configs.cli_logger import LOG_DATA_PATH


def create_logs_dump(path, filter_container=None):
    dump_folder_path, dump_folder_name = create_dump_dir()

    containers_logs_path = os.path.join(dump_folder_path, 'containers')
    cli_logs_path = os.path.join(dump_folder_path, 'cli')
    removed_containers_logs_path = os.path.join(dump_folder_path, 'removed_containers')
    archive_path = os.path.join(path, f'{dump_folder_name}.tar.gz')

    if filter_container:
        containers = get_containers(filter_container)
    else:
        containers = get_containers('skale')

    for container in containers:
        log_filepath = os.path.join(containers_logs_path, f'{container.name}.log')
        save_container_logs(container, log_filepath, tail='all')

    shutil.copytree(LOG_DATA_PATH, cli_logs_path)
    shutil.copytree(REMOVED_CONTAINERS_FOLDER_PATH, removed_containers_logs_path)
    create_archive(archive_path, dump_folder_path)
    if not os.path.isfile(archive_path):
        return None
    return archive_path


def create_dump_dir():
    time = datetime.datetime.utcnow().strftime("%Y-%m-%d-%H:%M:%S")
    folder_name = f'skale-logs-dump-{time}'
    folder_path = os.path.join('/tmp', folder_name)
    containers_path = os.path.join(folder_path, 'containers')
    safe_mk_dirs(containers_path)
    return folder_path, folder_name


def create_archive(archive_path, source_path):
    cmd = shlex.split(f'tar -czvf {archive_path} -C {source_path} .')
    run_cmd(cmd)
