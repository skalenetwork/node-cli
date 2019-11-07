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

import requests

from tests.helper import response_mock, run_command_mock
from cli.metrics import first, last


def test_metrics(skip_auth, config):
    response_data = {
        'bounties': [
            ['2019-10-09 02:46:50', 4018775720164609053497, 0, 1],
            ['2019-10-09 03:47:00', 4018775720164609053497, 0, 1],
            ['2019-10-09 04:47:11', 4018775720164609053497, 0, 1],
            ['2019-10-09 05:47:21', 4018775720164609053497, 0, 1],
            ['2019-10-09 06:47:32', 4018775720164609053497, 0, 1]
        ]
    }
    resp_mock = response_mock(
        requests.codes.ok,
        json_data={'data': response_data, 'res': 1}
    )
    result = run_command_mock('core.helper.get_request', resp_mock, first)
    assert result.exit_code == 0
    assert result.output == 'Please wait - collecting metrics from blockchain...\n       Date                   Bounty           Downtime   Latency\n-----------------------------------------------------------------\n2019-10-09 02:46:50   4018775720164609053497   0          1      \n2019-10-09 03:47:00   4018775720164609053497   0          1      \n2019-10-09 04:47:11   4018775720164609053497   0          1      \n2019-10-09 05:47:21   4018775720164609053497   0          1      \n2019-10-09 06:47:32   4018775720164609053497   0          1      \n'  # noqa

    result = run_command_mock('core.helper.get_request', resp_mock, first)
    assert result.exit_code == 0
    assert result.output == 'Please wait - collecting metrics from blockchain...\n       Date                   Bounty           Downtime   Latency\n-----------------------------------------------------------------\n2019-10-09 02:46:50   4018775720164609053497   0          1      \n2019-10-09 03:47:00   4018775720164609053497   0          1      \n2019-10-09 04:47:11   4018775720164609053497   0          1      \n2019-10-09 05:47:21   4018775720164609053497   0          1      \n2019-10-09 06:47:32   4018775720164609053497   0          1      \n'  # noqa

    for func in (first, last):
        resp_mock = response_mock(
            requests.codes.ok,
            json_data={'data': {'bounties': []}, 'res': 1}
        )
        result = run_command_mock('core.helper.get_request', resp_mock, func)
        assert result.exit_code == 0
        assert result.output == 'Please wait - collecting metrics from blockchain...\nNo bounties found\n'  # noqa
