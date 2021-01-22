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


from core.operations.common import (
    remove_compose_containers, remove_dynamic_containers, backup_old_contracts,
    download_contracts, docker_lvmpy_update, download_skale_node_release, run_compose_containers)


def update(env):
    remove_compose_containers(env)
    remove_dynamic_containers()

    backup_old_contracts()
    download_contracts(env)
    docker_lvmpy_update()

    download_skale_node_release()
    run_compose_containers()


def init(env):
    pass


def backup_init(env):
    pass


def turn_off(env):
    pass


def turn_on(env):
    pass
