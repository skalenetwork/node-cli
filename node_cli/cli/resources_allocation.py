#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
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

import json
import click

from node_cli.core.resources import (
    get_resource_allocation_info,
    generate_resource_allocation_config
)
from node_cli.utils.helper import abort_if_false, safe_load_texts

TEXTS = safe_load_texts()


@click.group()
def resources_allocation_cli():
    pass


@resources_allocation_cli.group(help="Resources allocation commands")
def resources_allocation():
    pass


@resources_allocation.command('show', help="Show resources allocation file")
def show():
    resource_allocation_info = get_resource_allocation_info()
    if resource_allocation_info:
        print(json.dumps(resource_allocation_info, indent=4))
    else:
        print('No resources allocation file on this machine')


@resources_allocation.command('generate',
                              help="Generate/update resources allocation file")
@click.argument('env_file')
@click.option(
    '--yes', is_flag=True, callback=abort_if_false,
    expose_value=False,
    prompt='Are you sure you want to generate/update resource allocation file?'
)
@click.option('--force', '-f', is_flag=True,
              help='Rewrite if already exists')
def generate(env_file, force):
    generate_resource_allocation_config(env_file=env_file, force=force)
