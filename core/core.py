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

import inspect
from configs import LONG_LINE
from core.helper import get_request, safe_load_texts
from core.print_formatters import print_err_response

NODE_STATUSES = ['Active', 'Leaving', 'Frozen', 'Left', 'Not created']
TEXTS = safe_load_texts()


def get_node_info(config, format):
    status, payload = get_request('node_info')
    if status == 'ok':
        node_info = payload['node_info']
        if node_info['status'] == 0:
            print(TEXTS['service']['node_not_registered'])
        elif format == 'json':
            print(node_info)
        else:
            print_node_info(node_info)
    else:
        print_err_response(payload)


def get_node_about(config, format):
    status, payload = get_request('node_about')
    if status == 'ok':
        print(payload)
    else:
        print_err_response(payload)


def get_node_status(status):
    return NODE_STATUSES[status]


def print_node_info(node):
    print(inspect.cleandoc(f'''
        {LONG_LINE}
        Node info
        Name: {node['name']}
        IP: {node['ip']}
        Public IP: {node['publicIP']}
        Port: {node['port']}
        Status: {get_node_status(int(node['status']))}
        {LONG_LINE}
    '''))
