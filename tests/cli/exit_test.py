import requests
from node_cli.cli.exit import status

from tests.helper import response_mock, run_command_mock


def test_exit_status():
    payload = {
        'status': 'ACTIVE',
        'data': [{'name': 'test', 'status': 'ACTIVE'}],
        'exit_time': 0
    }

    resp_mock = response_mock(
        requests.codes.ok,
        json_data={'payload': payload, 'status': 'ok'}
    )
    result = run_command_mock(
        'node_cli.utils.helper.requests.get', resp_mock, status, ['--format', 'json'])
    assert result.exit_code == 0
    assert result.output == "{'status': 'ACTIVE', 'data': [{'name': 'test', 'status': 'ACTIVE'}], 'exit_time': 0}\n" # noqa
