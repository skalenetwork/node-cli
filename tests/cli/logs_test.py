import os

import mock
import requests

from io import BytesIO
from tests.helper import response_mock, run_command
from cli.logs import dump


def test_get_schain_conget_schain_config(config, skip_auth):
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
