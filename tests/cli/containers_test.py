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
