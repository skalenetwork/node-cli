#   -*- coding: utf-8 -*-
#
#   This file is part of skale-node-cli
#
#   Copyright (C) 2019 SKALE Labs
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

import click
from core.helper import get
from core.print_formatters import print_containers


@click.group()
def containers_cli():
    pass


@containers_cli.group('containers', help="Node containers commands")
def containers():
    pass


@containers.command(help="List of sChain containers running on connected node")
@click.option('--all', '-a', is_flag=True)
def schains(all):
    response = get('schains_containers', {'all': all})
    if response is None:
        return
    if 'errors' in response:
        print(response['errors'])
    print_containers(response)


@containers.command(help="List of SKALE containers running on connected node")
@click.option('--all', '-a', is_flag=True)
def ls(all):
    containers_list = get('skale_containers', {'all': all})
    if not containers_list:
        return
    print_containers(containers_list)
