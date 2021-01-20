#   -*- coding: utf-8 -*-
#
#   This file is part of SKALE Admin
#
#   Copyright (C) 2020 SKALE Labs
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


CURRENT_API_VERSION = 'v1'
API_PREFIX = '/api'

ROUTES = {
    'v1': {
        'logs': ['dump'],
        'node': ['info', 'register', 'maintenance-on', 'maintenance-off', 'signature',
                 'send-tg-notification', 'exit/start', 'exit/status', 'set-domain-name'],
        'health': ['containers', 'schains', 'sgx'],
        'schains': ['config', 'list', 'dkg-statuses', 'firewall-rules', 'repair', 'get'],
        'ssl': ['status', 'upload'],
        'wallet': ['info', 'send-eth']
    }
}


class RouteNotFoundException(Exception):
    """Raised when requested route is not found in provided API version"""


def route_exists(blueprint, method, api_version):
    return ROUTES.get(api_version) and ROUTES[api_version].get(blueprint) and \
        method in ROUTES[api_version][blueprint]


def get_route(blueprint, method, api_version=CURRENT_API_VERSION, check=True):
    route = os.path.join(API_PREFIX, api_version, blueprint, method)
    if check and not route_exists(blueprint, method, api_version):
        raise RouteNotFoundException(route)
    return route


def get_all_available_routes(api_version=CURRENT_API_VERSION):
    routes = ROUTES[api_version]
    return [get_route(blueprint, method, api_version) for blueprint in routes
            for method in routes[blueprint]]
