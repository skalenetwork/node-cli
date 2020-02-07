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


import os

import mock
import requests

from io import BytesIO
from tests.helper import response_mock, run_command
from cli.logs import dump


def test_dump(config):
    archive_filename = 'skale-logs-dump-2019-10-08-17:40:00.tar.gz'
    resp_mock = response_mock(
        requests.codes.ok,
        headers={
            'Content-Disposition': f'attachment; filename="{archive_filename}"'
        },
        raw=BytesIO()
    )
    with mock.patch('requests.get') as req_get_mock:
        req_get_mock.return_value.__enter__.return_value = resp_mock
        result = run_command(dump, ['.'])
        assert result.exit_code == 0
        assert result.output == f'File {archive_filename} downloaded\n'

    if os.path.exists(archive_filename):
        os.remove(archive_filename)
