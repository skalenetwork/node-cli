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

from configs import ROUTES
from core.helper import get_node_creds, construct_url, get_request


def get_validators_info(config, format):
    cookies = get_node_creds(config)
    url = construct_url(ROUTES['validators_info'])

    response = get_request(url, cookies)
    if response is None:
        return None

    json = response.json()
    data = json['data']

    if format == 'json':
        print(data)
