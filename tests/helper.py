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

import mock
from click.testing import CliRunner
from mock import Mock, MagicMock


def response_mock(status_code=0, json_data=None,
                  headers=None, raw=None):
    result = MagicMock()
    result.status_code = status_code

    result.json = MagicMock(return_value=json_data)
    result.headers = headers
    result.raw = raw
    return result


def request_mock(response_mock):
    request_mock = Mock(return_value=response_mock)
    return request_mock


def run_command(command, params=[], input=''):
    runner = CliRunner()
    return runner.invoke(command, params, input=input)


def run_command_mock(mock_call_path, response_mock,
                     command, params=[], input=''):
    with mock.patch(mock_call_path,
                    new=request_mock(response_mock)):
        return run_command(command, params, input=input)


def subprocess_run_mock(cmd=None, shell=None, stdout=None,
                        stderr=None, env=None, returncode=0):
    result = MagicMock()
    result.returncode = returncode
    result.stdout = MagicMock()
    result.stderr = MagicMock()
    return result
