import mock
import requests

from io import BytesIO
from tests.helper import response_mock, run_command
from cli.logs import dump


def test_get_schain_conget_schain_config(config, skip_auth):
    response_data = {}
    resp_mock = response_mock(
        requests.codes.ok,
        json_data={'data': response_data, 'res': 1},
        headers={
            'Content-Disposition': 'attachment; filename="skale-logs-dump-2019-10-08-17:40:00.tar.gz"'  # noqa
        },
        raw=BytesIO()
    )
    with mock.patch('requests.get') as req_get_mock:
        req_get_mock.return_value.__enter__.return_value = resp_mock
        result = run_command(dump, ['.'])
        assert result.exit_code == 0
        assert result.output == 'File skale-logs-dump-2019-10-08-17:40:00.tar.gz downloaded\n'  # noqa
