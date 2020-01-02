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

from tests.helper import response_mock, run_command_mock
from cli.containers import ls, schains


RESPONSE_DATA = [
    {
        'image': 'image-skale', 'name': 'skale_schain_test',
        'state': {
            'Status': 'running', 'Running': True, 'Paused': False,
            'Restarting': False, 'OOMKilled': False, 'Dead': False,
            'Pid': 123, 'ExitCode': 0, 'Error': '',
            'StartedAt': '2019-10-08T13:59:54.52368097Z',
            'FinishedAt': '0001-01-01T00:00:00Z'
        }
    },
    {
        'image': 'image-skale', 'name': 'skale_schain_test2',
        'state': {
            'Status': 'running', 'Running': False, 'Paused':  True,
            'Restarting': False, 'OOMKilled': False, 'Dead': False,
            'Pid': 124, 'ExitCode': 0, 'Error': '',
            'StartedAt': '2019-10-08T13:59:54.52368099Z',
            'FinishedAt': '0001-01-01T00:00:00Z'
        }
     }
]


def test_schains(skip_auth, config):
    resp_mock = response_mock(
        requests.codes.ok,
        json_data={'data': RESPONSE_DATA, 'res': 1}
    )
    result = run_command_mock('core.helper.get_request', resp_mock, schains)
    assert result.exit_code == 0
    assert result.output == "       Name                    Status                   Started At           Image   \n-------------------------------------------------------------------------------------\nskale_schain_test    Running                       Oct 08 2019 13:59:54   image-skale\nskale_schain_test2   Running (Jan 01 1 00:00:00)   Oct 08 2019 13:59:54   image-skale\n"  # noqa

    resp_mock = response_mock(
        requests.codes.ok,
        json_data={'data': RESPONSE_DATA, 'res': 0}
    )
    result = run_command_mock('core.helper.get_request', resp_mock, schains)
    assert result.exit_code == 1
    assert result.output == ('----------------------------------'
                             '----------------\n')

    resp_mock = response_mock(
        requests.codes.ok,
        None
    )
    result = run_command_mock('core.helper.get_request', resp_mock, schains)
    assert result.exit_code == 1
    assert result.output == ''

    resp_mock = response_mock(
        -1,
        {'data': RESPONSE_DATA, 'res': 1}
    )
    result = run_command_mock('core.helper.get_request', resp_mock, schains)
    assert result.exit_code == 0
    assert result.output == 'Request failed, status code: -1\n'


def test_ls():
    resp_mock = response_mock(
        requests.codes.ok,
        json_data={'data': RESPONSE_DATA, 'res': 1}
    )
    result = run_command_mock('core.helper.get_request', resp_mock, ls)
    assert result.exit_code == 0
    assert result.output == '       Name                    Status                   Started At           Image   \n-------------------------------------------------------------------------------------\nskale_schain_test    Running                       Oct 08 2019 13:59:54   image-skale\nskale_schain_test2   Running (Jan 01 1 00:00:00)   Oct 08 2019 13:59:54   image-skale\n'  # noqa
