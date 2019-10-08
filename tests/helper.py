import mock
from click.testing import CliRunner
from mock import Mock, MagicMock


def response_mock(status_code=0, json_data=None, cookies=None,
                  headers=None, raw=None):
    result = MagicMock()
    result.status_code = status_code
    result.json = MagicMock(return_value=json_data)
    result.cookies = cookies
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
