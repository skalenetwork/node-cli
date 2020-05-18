#   -*- coding: utf-8 -*-
#
#   This file is part of skale-node-cli
#
#   Copyright (C) 2019-2020 SKALE Labs
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
from cli.metrics import metrics

OK_RESPONSE_DATA = {
    'status': 'ok',
    'payload': {
        'metrics': [
            ['2019-10-09 02:46:50', 4018775720164609053497, 0, 1],
            ['2019-10-09 03:47:00', 4018775720164609053497, 0, 1],
            ['2019-10-09 04:47:11', 4018775720164609053497, 0, 1],
            ['2019-10-09 05:47:21', 4018775720164609053497, 0, 1],
            ['2019-10-09 06:47:32', 4018775720164609053497, 0, 1]
        ],
        'total': 4018.7759
    }
}


def test_metrics_ok(config):
    resp_mock = response_mock(
        requests.codes.ok,
        json_data=OK_RESPONSE_DATA
    )
    result = run_command_mock('core.helper.requests.get', resp_mock, metrics)
    assert result.exit_code == 0

    expected_output = f'Please wait - collecting metrics data from blockchain...\n' \
                      f'+---------------------------------------------------------------------+\n'\
                      f'|        Date                    Bounty            Downtime   Latency |\n'\
                      f'+---------------------------------------------------------------------+\n'\
                      f'| 2019-10-09 02:46:50   4018775720164608966656.0          0       1.0 |\n'\
                      f'| 2019-10-09 03:47:00   4018775720164608966656.0          0       1.0 |\n'\
                      f'| 2019-10-09 04:47:11   4018775720164608966656.0          0       1.0 |\n'\
                      f'| 2019-10-09 05:47:21   4018775720164608966656.0          0       1.0 |\n'\
                      f'| 2019-10-09 06:47:32   4018775720164608966656.0          0       1.0 |\n'\
                      f'+---------------------------------------------------------------------+\n'\
                      f'Total bounty per the given period: 4018.776 SKL\n'
    assert result.output == expected_output


def test_metrics_empty_results(config):
    resp_mock = response_mock(
        requests.codes.ok,
        json_data={'status': 'ok', 'payload': {'metrics': [], 'total': 0}}
    )
    result = run_command_mock('core.helper.requests.get', resp_mock, metrics)
    assert result.exit_code == 0
    expected_output = f'Please wait - collecting metrics data from blockchain...\n' \
                      f'+------------------------------------+\n'\
                      f'| Date   Bounty   Downtime   Latency |\n'\
                      f'+------------------------------------+\n' \
                      f'+------------------------------------+\n' \
                      f'Total bounty per the given period: 0.000 SKL\n'
    assert result.output == expected_output


def test_metrics_wei(config):
    # test --wei
    resp_mock = response_mock(
        requests.codes.ok,
        json_data=OK_RESPONSE_DATA
    )
    result = run_command_mock('core.helper.requests.get', resp_mock, metrics, ['--wei'])
    assert result.exit_code == 0

    expected_output = f'Please wait - collecting metrics data from blockchain...\n' \
                      f'+-------------------------------------------------------------------+\n' \
                      f'|        Date                   Bounty           Downtime   Latency |\n' \
                      f'+-------------------------------------------------------------------+\n' \
                      f'| 2019-10-09 02:46:50   4018775720164608966656          0       1.0 |\n' \
                      f'| 2019-10-09 03:47:00   4018775720164608966656          0       1.0 |\n' \
                      f'| 2019-10-09 04:47:11   4018775720164608966656          0       1.0 |\n' \
                      f'| 2019-10-09 05:47:21   4018775720164608966656          0       1.0 |\n' \
                      f'| 2019-10-09 06:47:32   4018775720164608966656          0       1.0 |\n' \
                      f'+-------------------------------------------------------------------+\n' \
                      f'Total bounty per the given period: 4018.7759 wei\n'
    assert result.output == expected_output


def test_metrics_fast(config):
    resp_mock = response_mock(
        requests.codes.ok,
        json_data=OK_RESPONSE_DATA
    )
    result = run_command_mock('core.helper.requests.get',
                              resp_mock, metrics, ['--fast'])
    assert result.exit_code == 0

    expected_output = f'+---------------------------------------------------------------------+\n'\
                      f'|        Date                    Bounty            Downtime   Latency |\n'\
                      f'+---------------------------------------------------------------------+\n'\
                      f'| 2019-10-09 02:46:50   4018775720164608966656.0          0       1.0 |\n'\
                      f'| 2019-10-09 03:47:00   4018775720164608966656.0          0       1.0 |\n'\
                      f'| 2019-10-09 04:47:11   4018775720164608966656.0          0       1.0 |\n'\
                      f'| 2019-10-09 05:47:21   4018775720164608966656.0          0       1.0 |\n'\
                      f'| 2019-10-09 06:47:32   4018775720164608966656.0          0       1.0 |\n'\
                      f'+---------------------------------------------------------------------+\n'\
                      f'Total bounty per the given period: 4018.776 SKL\n'
    assert result.output == expected_output


def test_metrics_fast_wei(config):
    resp_mock = response_mock(
        requests.codes.ok,
        json_data=OK_RESPONSE_DATA
    )
    result = run_command_mock('core.helper.requests.get', resp_mock, metrics, ['--wei', '--fast'])
    assert result.exit_code == 0

    expected_output = f'+-------------------------------------------------------------------+\n' \
                      f'|        Date                   Bounty           Downtime   Latency |\n' \
                      f'+-------------------------------------------------------------------+\n' \
                      f'| 2019-10-09 02:46:50   4018775720164608966656          0       1.0 |\n' \
                      f'| 2019-10-09 03:47:00   4018775720164608966656          0       1.0 |\n' \
                      f'| 2019-10-09 04:47:11   4018775720164608966656          0       1.0 |\n' \
                      f'| 2019-10-09 05:47:21   4018775720164608966656          0       1.0 |\n' \
                      f'| 2019-10-09 06:47:32   4018775720164608966656          0       1.0 |\n' \
                      f'+-------------------------------------------------------------------+\n' \
                      f'Total bounty per the given period: 4018.7759 wei\n'
    assert result.output == expected_output


def test_metrics_all_params(config):
    resp_mock = response_mock(
        requests.codes.ok,
        json_data=OK_RESPONSE_DATA
    )
    result = run_command_mock('core.helper.requests.get',
                              resp_mock, metrics,
                              ['--since', '2019-10-09', '--till', '2019-10-10', '--limit', 5,
                               '--wei', '--fast'])

    expected_output = f'+-------------------------------------------------------------------+\n' \
                      f'|        Date                   Bounty           Downtime   Latency |\n' \
                      f'+-------------------------------------------------------------------+\n' \
                      f'| 2019-10-09 02:46:50   4018775720164608966656          0       1.0 |\n' \
                      f'| 2019-10-09 03:47:00   4018775720164608966656          0       1.0 |\n' \
                      f'| 2019-10-09 04:47:11   4018775720164608966656          0       1.0 |\n' \
                      f'| 2019-10-09 05:47:21   4018775720164608966656          0       1.0 |\n' \
                      f'| 2019-10-09 06:47:32   4018775720164608966656          0       1.0 |\n' \
                      f'+-------------------------------------------------------------------+\n' \
                      f'Total bounty per the given period: 4018.7759 wei\n'
    assert result.exit_code == 0
    assert result.output == expected_output
