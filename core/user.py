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

import requests
import logging
import pickle
import json
from configs import ROUTES, TOKENS_FILEPATH
from core.helper import construct_url, clean_cookies, get_request, post_request

logger = logging.getLogger(__name__)


def register_user(config, username, password, token):
    data = {
        'username': username,
        'password': password,
        'token': token
    }
    url = construct_url(ROUTES['register'])
    response = post_request(url, data)
    if response is None:
        return None
    if response.status_code == requests.codes.ok:
        cookies_text = pickle.dumps(response.cookies)
        config['cookies'] = cookies_text
        print(f'User created: {username}')
        print('Success, cookies saved.')
    else:
        print('Registration failed: ' + response.text)


def login_user(config, username, password):
    data = {
        'username': username,
        'password': password
    }
    url = construct_url(ROUTES['login'])
    response = post_request(url, data)
    if response is None:
        return None

    if response.status_code == requests.codes.ok:
        cookies_text = pickle.dumps(response.cookies)
        config['cookies'] = cookies_text
        print('Success, cookies saved.')
    else:
        print('Authorization failed: ' + response.text)


def logout_user(config):
    url = construct_url(ROUTES['logout'])
    response = get_request(url)
    if response is None:
        return None

    if response.status_code == requests.codes.ok:
        clean_cookies(config)
        print('Cookies removed')
    else:
        print('Logout failed:')
        print(response.text)


def get_registration_token_data():
    try:
        with open(TOKENS_FILEPATH, encoding='utf-8') as data_file:
            return json.loads(data_file.read())
    except FileNotFoundError:
        return None


def show_registration_token(short):
    token_data = get_registration_token_data()
    if token_data is not None:
        if short:
            print(token_data["token"])
        else:
            print(f'User registration token: {token_data["token"]}')
    else:
        err_msg = ("Couldn't find registration tokens file. "
                   "Check that node inited on this machine.")
        logger.error(err_msg)
        print(err_msg)
