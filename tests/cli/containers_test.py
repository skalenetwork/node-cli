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

import requests

from tests.helper import response_mock, run_command_mock
from cli.containers import ls, schains


OK_RESPONSE_DATA = {
    'status': 'ok',
    'payload': [{
        'image': 'image-skale', 'name': 'skale_schain_test',
        'state': {
            'Status': 'running', 'Running': True, 'Paused': False,
            'Restarting': False, 'OOMKilled': False, 'Dead': False,
            'Pid': 123, 'ExitCode': 0, 'Error': '',
            'StartedAt': '2019-10-08T13:59:54.52368097Z',
            'FinishedAt': '0001-01-01T00:00:00Z'
        }
    }, {
        'image': 'image-skale', 'name': 'skale_schain_test2',
        'state': {
            'Status': 'running', 'Running': False, 'Paused': True,
            'Restarting': False, 'OOMKilled': False, 'Dead': False,
            'Pid': 124, 'ExitCode': 0, 'Error': '',
            'StartedAt': '2019-10-08T13:59:54.52368099Z',
            'FinishedAt': '0001-01-01T00:00:00Z'
        }
     }
    ]}


OK_LS_RESPONSE_DATA = {
    'status': 'ok',
    'payload':
        {'containers': [{'image': 'skalenetwork/schain:1.46-develop.21',
                         'name': 'skale_schain_shapely-alfecca-meridiana',
                         'state': {
                             'Status': 'running', 'Running': True,
                             'Paused': False, 'Restarting': False,
                             'OOMKilled': False, 'Dead': False,
                             'Pid': 232, 'ExitCode': 0,
                             'Error': '',
                             'StartedAt': '2020-07-31T11:56:35.732888232Z',
                             'FinishedAt': '0001-01-01T00:00:00Z'}
                         },
                        {'image': 'skale-admin:latest', 'name': 'skale_api',
                         'state': {
                             'Status': 'running',
                             'Running': True, 'Paused': False,
                             'Restarting': False, 'OOMKilled': False,
                             'Dead': False, 'Pid': 6710, 'ExitCode': 0,
                             'Error': '',
                             'StartedAt': '2020-07-31T11:55:17.28700307Z',
                             'FinishedAt': '0001-01-01T00:00:00Z'}}]
         }}


def test_schains_ok_response(config):
    resp_mock = response_mock(
        requests.codes.ok,
        json_data=OK_RESPONSE_DATA
    )
    result = run_command_mock('core.helper.requests.get',
                              resp_mock, schains)
    assert result.exit_code == 0
    assert result.output == "       Name                    Status                   Started At           Image   \n-------------------------------------------------------------------------------------\nskale_schain_test    Running                       Oct 08 2019 13:59:54   image-skale\nskale_schain_test2   Running (Jan 01 1 00:00:00)   Oct 08 2019 13:59:54   image-skale\n"  # noqa


def test_schain_error_response(config):
    resp_mock = response_mock(
        requests.codes.bad_request,
        json_data={'status': 'error', 'payload': 'Operation failed'}
    )
    result = run_command_mock('core.helper.requests.get',
                              resp_mock, schains)
    assert result.exit_code == 0
    print(repr(result.output))
    assert result.output == ('Command failed with following errors:\n'
                             '-----------------------------------------'
                             '---------\nOperation failed\n--------------------'
                             '------------------------------\n')


def test_schain_empty_response(config):
    resp_mock = response_mock(
        requests.codes.ok,
        {'status': 'ok', 'payload': None}
    )
    result = run_command_mock('core.helper.requests.get',
                              resp_mock, schains)
    assert result.exit_code == 1
    assert result.output == ''


def test_schain_multi_error_response(config):
    resp_mock = response_mock(
        -1,
        {'payload': ['Error test', 'Error test2'], 'status': 'error'}
    )
    result = run_command_mock('core.helper.requests.get',
                              resp_mock, schains)
    assert result.exit_code == 0
    print(repr(result.output))
    assert result.output == 'Command failed with following errors:\n--------------------------------------------------\nError test\nError test2\n--------------------------------------------------\n'  # noqa


def test_ls():
    resp_mock = response_mock(
        requests.codes.ok,
        json_data=OK_LS_RESPONSE_DATA
    )
    result = run_command_mock('core.helper.requests.get',
                              resp_mock, ls)
    assert result.exit_code == 0
    assert result.output == '                 Name                    Status         Started At                       Image               \n-------------------------------------------------------------------------------------------------------------\nskale_schain_shapely-alfecca-meridiana   Running   Jul 31 2020 11:56:35   skalenetwork/schain:1.46-develop.21\nskale_api                                Running   Jul 31 2020 11:55:17   skale-admin:latest                 \n'  # noqa
