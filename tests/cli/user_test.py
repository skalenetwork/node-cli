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
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

import mock
import requests

from mock import MagicMock

from cli.user import login, logout, register, user_token
from tests.helper import run_command, run_command_mock


def test_user_token():
    test_token = '231test-token'
    with mock.patch('core.user.get_registration_token_data',
                    new=MagicMock(return_value={'token': test_token})):
        result = run_command(user_token)
        assert result.output == f'User registration token: {test_token}\n'
        result = run_command(user_token, ['--short'])
        assert result.output == '231test-token\n'

    with mock.patch('core.user.get_registration_token_data',
                    new=MagicMock(return_value=None)):
        result = run_command(user_token)
        assert result.exit_code == 0
        print(result.output)
        assert result.output == ("Couldn't find registration tokens file. "
                                 "Check that node initalized on this machine.\n")


def test_register(config):
    response_mock = MagicMock()
    response_mock.status_code = requests.codes.ok
    response_mock.cookies = 'cookies'
    result = run_command_mock('core.user.post_request',
                              response_mock,
                              register,
                              input="test\n qwerty1\n token")
    expected = (
        'Enter username: test\n'
        'Enter password: \n'
        'Enter one-time token: \n'
        'User created: test\n'
        'Success, cookies saved.\n'
    )
    assert result.exit_code == 0
    assert result.output == expected

    response_mock.status_code = -1
    response_mock.text = '{"errors": [{"msg": "Token not match"}]}'
    result = run_command_mock('core.user.post_request',
                              response_mock,
                              register,
                              input="test\n qwerty1\n token")
    assert result.exit_code == 0
    expected = (
        'Enter username: test\n'
        'Enter password: \n'
        'Enter one-time token: \n'
        'Registration failed: {"errors": [{"msg": "Token not match"}]}\n'
    )
    assert expected == result.output


def test_login(config):
    response_mock = MagicMock()
    response_mock.status_code = requests.codes.ok
    response_mock.cookies = 'simple-cookies'
    result = run_command_mock('core.user.post_request',
                              response_mock,
                              login,
                              input="test\n qwerty1\n token")
    expected = (
        'Enter username: test\n'
        'Enter password: \n'
        'Success, cookies saved.\n'
    )
    assert result.exit_code == 0
    assert result.output == expected

    response_mock.status_code = -1
    response_mock.text = '{"errors": [{"msg": "Test error"}]}'
    result = run_command_mock('core.user.post_request',
                              response_mock,
                              login,
                              input="test\n qwerty1")
    assert result.exit_code == 0
    expected = (
        'Enter username: test\n'
        'Enter password: \n'
        'Authorization failed: {"errors": [{"msg": "Test error"}]}\n'
    )
    print(result.output)
    assert expected == result.output


def test_logout(config):
    response_mock = MagicMock()
    response_mock.status_code = requests.codes.ok
    response_mock.cookies = 'simple-cookies'
    result = run_command_mock('core.user.get_request',
                              response_mock,
                              logout,
                              input="test\n qwerty1\n token")
    assert result.exit_code == 0
    expected = 'Cookies removed\n'
    assert result.output == expected

    response_mock.status_code = -1
    response_mock.text = '{"errors": [{"msg": "Test error"}]}'
    result = run_command_mock('core.user.get_request',
                              response_mock,
                              logout,
                              input="test\n qwerty1")
    assert result.exit_code == 0
    expected = (
        'Logout failed:\n'
        '{"errors": [{"msg": "Test error"}]}\n'
    )
    assert expected == result.output
