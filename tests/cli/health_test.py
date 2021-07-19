import requests

from tests.helper import response_mock, run_command_mock
from node_cli.cli.health import containers, schains, sgx


OK_LS_RESPONSE_DATA = {
    'status': 'ok',
    'payload':
        [
            {
                'image': 'skalenetwork/schain:1.46-develop.21',
                'name': 'skale_schain_shapely-alfecca-meridiana',
                'state': {
                    'Status': 'running', 'Running': True,
                    'Paused': False, 'Restarting': False,
                    'OOMKilled': False, 'Dead': False,
                    'Pid': 232, 'ExitCode': 0,
                    'Error': '',
                    'StartedAt': '2020-07-31T11:56:35.732888232Z',
                    'FinishedAt': '0001-01-01T00:00:00Z'
                }
            },
            {
                'image': 'skale-admin:latest', 'name': 'skale_api',
                'state': {
                    'Status': 'running',
                    'Running': True, 'Paused': False,
                    'Restarting': False, 'OOMKilled': False,
                    'Dead': False, 'Pid': 6710, 'ExitCode': 0,
                    'Error': '',
                    'StartedAt': '2020-07-31T11:55:17.28700307Z',
                    'FinishedAt': '0001-01-01T00:00:00Z'
                }
            }
        ]
}


def test_containers():
    resp_mock = response_mock(
        requests.codes.ok,
        json_data=OK_LS_RESPONSE_DATA
    )
    result = run_command_mock('node_cli.utils.helper.requests.get',
                              resp_mock, containers)
    assert result.exit_code == 0
    assert result.output == '                 Name                    Status         Started At                       Image               \n-------------------------------------------------------------------------------------------------------------\nskale_schain_shapely-alfecca-meridiana   Running   Jul 31 2020 11:56:35   skalenetwork/schain:1.46-develop.21\nskale_api                                Running   Jul 31 2020 11:55:17   skale-admin:latest                 \n'  # noqa


def test_checks():
    payload = [
        {
            "name": "test_schain",
            "healthchecks": {
                "data_dir": True,
                "dkg": False,
                "config": False,
                "volume": False,
                "container": False,
                "ima_container": False,
                "firewall_rules": False,
                "rpc": False,
                "blocks": False
            }
        }
    ]
    resp_mock = response_mock(
        requests.codes.ok,
        json_data={'payload': payload, 'status': 'ok'}
    )
    result = run_command_mock('node_cli.utils.helper.requests.get',
                              resp_mock, schains)

    print(result)
    print(result.output)

    assert result.exit_code == 0
    assert result.output == 'sChain Name   Data directory    DKG    Config file   Volume   Container    IMA    Firewall    RPC    Blocks\n-----------------------------------------------------------------------------------------------------------\ntest_schain   True             False   False         False    False       False   False      False   False \n'  # noqa

    result = run_command_mock('node_cli.utils.helper.requests.get',
                              resp_mock, schains, ['--json'])

    assert result.exit_code == 0
    assert result.output == '[{"name": "test_schain", "healthchecks": {"data_dir": true, "dkg": false, "config": false, "volume": false, "container": false, "ima_container": false, "firewall_rules": false, "rpc": false, "blocks": false}}]\n'  # noqa


def test_sgx_status():
    payload = {
        'sgx_server_url': 'https://127.0.0.1:1026',
        'sgx_wallet_version': '1.50.1-stable.0',
        'sgx_keyname': 'test_keyname',
        'status_name': 'CONNECTED'
    }
    resp_mock = response_mock(
        requests.codes.ok,
        json_data={'payload': payload, 'status': 'ok'}
    )
    result = run_command_mock(
        'node_cli.utils.helper.requests.get', resp_mock, sgx)

    assert result.exit_code == 0
    assert result.output == '\x1b(0lqqqqqqqqqqqqqqqqqqqwqqqqqqqqqqqqqqqqqqqqqqqqk\x1b(B\n\x1b(0x\x1b(B SGX info          \x1b(0x\x1b(B                        \x1b(0x\x1b(B\n\x1b(0tqqqqqqqqqqqqqqqqqqqnqqqqqqqqqqqqqqqqqqqqqqqqu\x1b(B\n\x1b(0x\x1b(B Server URL        \x1b(0x\x1b(B https://127.0.0.1:1026 \x1b(0x\x1b(B\n\x1b(0x\x1b(B SGXWallet Version \x1b(0x\x1b(B 1.50.1-stable.0        \x1b(0x\x1b(B\n\x1b(0x\x1b(B Node SGX keyname  \x1b(0x\x1b(B test_keyname           \x1b(0x\x1b(B\n\x1b(0x\x1b(B Status            \x1b(0x\x1b(B CONNECTED              \x1b(0x\x1b(B\n\x1b(0mqqqqqqqqqqqqqqqqqqqvqqqqqqqqqqqqqqqqqqqqqqqqj\x1b(B\n'  # noqa
