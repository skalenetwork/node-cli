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
import docker
from docker.client import DockerClient

logger = logging.getLogger(__name__)

SCHAIN_REMOVE_TIMEOUT = 40
IMA_REMOVE_TIMEOUT = 20


def docker_client() -> DockerClient:
    return docker.from_env()


def get_all_schain_containers(_all=False) -> list:
    return docker_client().containers.list(all=_all, filters={'name': 'skale_schain_*'})


def get_all_ima_containers(all=False, format=False) -> list:
    return docker_client().containers.list(all=all, filters={'name': 'skale_ima_*'})


def rm_all_schain_containers():
    schain_containers = get_all_schain_containers()
    remove_containers(schain_containers, timeout=SCHAIN_REMOVE_TIMEOUT)


def rm_all_ima_containers():
    ima_containers = get_all_ima_containers()
    remove_containers(ima_containers, timeout=IMA_REMOVE_TIMEOUT)


def remove_containers(containers, **kwargs):
    for container in containers:
        logger.info(f'Removing container: {container.name}')
        container.remove(**kwargs)
