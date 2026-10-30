import requests

from tests.helper import response_mock, run_command_mock
from node_cli.cli.health import containers, schains, sgx


OK_LS_RESPONSE_DATA = {
    'status': 'ok',
    'payload': [
        {
            'image': 'skalenetwork/schain:1.46-develop.21',
            'name': 'sk_skaled_shapely-alfecca-meridiana',
            'state': {
                'Status': 'running',
                'Running': True,
                'Paused': False,
                'Restarting': False,
                'OOMKilled': False,
                'Dead': False,
                'Pid': 232,
                'ExitCode': 0,
                'Error': '',
                'StartedAt': '2020-07-31T11:56:35.732888232Z',
                'FinishedAt': '0001-01-01T00:00:00Z',
            },
        },
        {
            'image': 'skale-admin:latest',
            'name': 'sk_api',
            'state': {
                'Status': 'running',
                'Running': True,
                'Paused': False,
                'Restarting': False,
                'OOMKilled': False,
                'Dead': False,
                'Pid': 6710,
                'ExitCode': 0,
                'Error': '',
                'StartedAt': '2020-07-31T11:55:17.28700307Z',
                'FinishedAt': '0001-01-01T00:00:00Z',
            },
        },
    ],
}


def test_containers():
    resp_mock = response_mock(requests.codes.ok, json_data=OK_LS_RESPONSE_DATA)
    result = run_command_mock('node_cli.utils.helper.api_session.get', resp_mock, containers)
    assert result.exit_code == 0
    assert (
        result.output
        == '               Name                   Status         Started At                       Image               \n----------------------------------------------------------------------------------------------------------\nsk_skaled_shapely-alfecca-meridiana   Running   Jul 31 2020 11:56:35   skalenetwork/schain:1.46-develop.21\nsk_api                                Running   Jul 31 2020 11:55:17   skale-admin:latest                 \n'  # noqa
    )


def test_checks():
    payload = [
        {
            'name': 'test_schain',
            'healthchecks': {
                'config_dir': True,
                'dkg': False,
                'config': False,
                'volume': False,
                'skaled_container': False,
                'ima_container': False,
                'firewall_rules': False,
                'rpc': False,
                'blocks': False,
            },
        }
    ]
    resp_mock = response_mock(requests.codes.ok, json_data={'payload': payload, 'status': 'ok'})
    result = run_command_mock('node_cli.utils.helper.api_session.get', resp_mock, schains)

    assert result.exit_code == 0
    assert (
        result.output
        == 'sChain Name   Config directory    DKG    Config file   Volume   Container    IMA    Firewall    RPC    Blocks\n-------------------------------------------------------------------------------------------------------------\ntest_schain   True               False   False         False    False       False   False      False   False \n'  # noqa
    )

    result = run_command_mock(
        'node_cli.utils.helper.api_session.get', resp_mock, schains, ['--json']
    )

    assert result.exit_code == 0
    assert (
        result.output
        == '[{"name": "test_schain", "healthchecks": {"config_dir": true, "dkg": false, "config": false, "volume": false, "skaled_container": false, "ima_container": false, "firewall_rules": false, "rpc": false, "blocks": false}}]\n'  # noqa
    )


def test_sgx_status():
    payload = {
        'sgx_server_url': 'https://127.0.0.1:1026',
        'sgx_wallet_version': '1.50.1-stable.0',
        'sgx_keyname': 'test_keyname',
        'status_zmq': True,
        'status_https': True,
    }
    resp_mock = response_mock(requests.codes.ok, json_data={'payload': payload, 'status': 'ok'})
    result = run_command_mock('node_cli.utils.helper.api_session.get', resp_mock, sgx)

    assert result.exit_code == 0
    assert result.output == (
        '    SGX info                              \n'
        '------------------------------------------\n'
        'Server URL          https://127.0.0.1:1026\n'
        'SGXWallet Version   1.50.1-stable.0       \n'
        'Node SGX keyname    test_keyname          \n'
        'Status HTTPS        True                  \n'
        'Status ZMQ          True                  \n'
    )
