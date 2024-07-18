#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
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
import time

import requests

from node_cli.configs import G_CONF_HOME
from tests.helper import response_mock, run_command, run_command_mock
from node_cli.cli.schains import (get_schain_config, ls, dkg, show_rules,
                                  repair, info_)


def test_ls():
    os.environ['TZ'] = 'Europe/London'
    time.tzset()
    payload = [
        {
            'name': 'test_schain1', 'mainnetOwner': '0x123',
            'indexInOwnerList': 3, 'partOfNode': 0,
            'lifetime': 5, 'startDate': 1570115385,
            'deposit': 1000000000000000000, 'index': 3, 'generation': 1, 'originator': '0x465'
        },
        {
            'name': 'crazy_cats1',
            'mainnetOwner': '0x321',
            'indexInOwnerList': 8, 'partOfNode': 0,
            'lifetime': 5, 'startDate': 1570469410,
            'deposit': 1000000000000000000, 'index': 8, 'generation': 0, 'originator': '0x0'
        }
    ]
    resp_mock = response_mock(
        requests.codes.ok,
        json_data={'payload': payload, 'status': 'ok'}
    )
    result = run_command_mock('node_cli.utils.helper.requests.get', resp_mock, ls)
    assert result.exit_code == 0
    assert result.output == '    Name       Owner   Size   Lifetime        Created At              Deposit         Generation   Originator\n-------------------------------------------------------------------------------------------------------------\ntest_schain1   0x123   0      5          Oct 03 2019 16:09:45   1000000000000000000   1            0x465     \ncrazy_cats1    0x321   0      5          Oct 07 2019 18:30:10   1000000000000000000   0            0x0       \n'  # noqa


def test_dkg():
    os.environ['TZ'] = 'Europe/London'
    time.tzset()
    payload = [
        {
            'name': 'melodic-aldhibah',
            'added_at': 1578497212.645233,
            'dkg_status': 2,
            'dkg_status_name': 'IN_PROGRESS',
            'is_deleted': False
        }
    ]
    resp_mock = response_mock(
        requests.codes.ok,
        json_data={'payload': payload, 'status': 'ok'}
    )
    result = run_command_mock('node_cli.utils.helper.requests.get',
                              resp_mock, dkg)
    assert result.exit_code == 0
    assert result.output == '  sChain Name      DKG Status          Added At         sChain Status\n---------------------------------------------------------------------\nmelodic-aldhibah   IN_PROGRESS   Jan 08 2020 15:26:52   Exists       \n'  # noqa

    result = run_command_mock('node_cli.utils.helper.requests.get',
                              resp_mock, dkg, ['--all'])
    assert result.exit_code == 0
    assert result.output == '  sChain Name      DKG Status          Added At         sChain Status\n---------------------------------------------------------------------\nmelodic-aldhibah   IN_PROGRESS   Jan 08 2020 15:26:52   Exists       \n'  # noqa


def test_get_schain_config():
    payload = {
        'nodeInfo': {
            'nodeID': 2, 'nodeName': 'testnet-1',
            'basePort': 10011, 'httpRpcPort': 10009,
            'httpsRpcPort': 11118, 'wsRpcPort': 10118,
            'wssRpcPort': 13219,
            'bindIP': '123.123.123.123'
        },
        'sChain': {
            'schainID': 1, 'schainName': 'test1',
            'nodes': [
                {'nodeID': 2,
                 'nodeName': 'testnet-1',
                 'basePort': 10011,
                 'httpRpcPort': 10013,
                 'httpsRpcPort': 10018,
                 'wsRpcPort': 10014,
                 'wssRpcPort': 10019,
                 'publicKey': 'public_key',
                 'owner': '0xe3213',
                 'schainIndex': 1,
                 'ip': '213.13.123.13',
                 'publicIP': '1.1.1.1'
                 },
                {'nodeID': 0, 'nodeName': 'testnet-2',
                 'basePort': 10077, 'httpRpcPort': 10079,
                 'httpsRpcPort': 10084, 'wsRpcPort': 10080,
                 'wssRpcPort': 10085,
                 'publicKey': 'public_key352',
                 'owner': '0x323',
                 'schainIndex': 2, 'ip': '2.2.2.2',
                 'publicIP': '3.3.3.3'
                 }]}
    }
    resp_mock = response_mock(
        requests.codes.ok,
        json_data={'payload': payload, 'status': 'ok'}
    )
    result = run_command_mock('node_cli.utils.helper.requests.get',
                              resp_mock,
                              get_schain_config, ['test1'])
    assert result.exit_code == 0
    assert result.output == "{'nodeInfo': {'basePort': 10011,\n              'bindIP': '123.123.123.123',\n              'httpRpcPort': 10009,\n              'httpsRpcPort': 11118,\n              'nodeID': 2,\n              'nodeName': 'testnet-1',\n              'wsRpcPort': 10118,\n              'wssRpcPort': 13219},\n 'sChain': {'nodes': [{'basePort': 10011,\n                       'httpRpcPort': 10013,\n                       'httpsRpcPort': 10018,\n                       'ip': '213.13.123.13',\n                       'nodeID': 2,\n                       'nodeName': 'testnet-1',\n                       'owner': '0xe3213',\n                       'publicIP': '1.1.1.1',\n                       'publicKey': 'public_key',\n                       'schainIndex': 1,\n                       'wsRpcPort': 10014,\n                       'wssRpcPort': 10019},\n                      {'basePort': 10077,\n                       'httpRpcPort': 10079,\n                       'httpsRpcPort': 10084,\n                       'ip': '2.2.2.2',\n                       'nodeID': 0,\n                       'nodeName': 'testnet-2',\n                       'owner': '0x323',\n                       'publicIP': '3.3.3.3',\n                       'publicKey': 'public_key352',\n                       'schainIndex': 2,\n                       'wsRpcPort': 10080,\n                       'wssRpcPort': 10085}],\n            'schainID': 1,\n            'schainName': 'test1'}}\n"  # noqa


def test_schain_rules():
    payload = {
        'endpoints': [
            {'port': 10000, 'first_ip': '127.0.0.2', 'last_ip': '127.0.0.2'},
            {'port': 10001, 'first_ip': '127.0.0.2', 'last_ip': '127.0.0.2'},
            {'port': 10002, 'first_ip': None, 'last_ip': None},
            {'port': 10003, 'first_ip': None, 'last_ip': None},
            {'port': 10004, 'first_ip': '127.0.0.2', 'last_ip': '127.0.0.2'},
            {'port': 10005, 'first_ip': '127.0.0.2', 'last_ip': '127.0.0.2'},
            {'port': 10007, 'first_ip': None, 'last_ip': None},
            {'port': 10008, 'first_ip': None, 'last_ip': None},
            {'port': 10009, 'first_ip': None, 'last_ip': None}
        ]
    }
    resp_mock = response_mock(
        requests.codes.ok,
        json_data={'payload': payload, 'status': 'ok'}
    )
    result = run_command_mock(
        'node_cli.utils.helper.requests.get', resp_mock, show_rules, ['schain-test'])
    assert result.exit_code == 0
    print(repr(result.output))
    assert result.output == '      IP range          Port \n-----------------------------\n127.0.0.2 - 127.0.0.2   10000\n127.0.0.2 - 127.0.0.2   10001\nAll IPs                 10002\nAll IPs                 10003\n127.0.0.2 - 127.0.0.2   10004\n127.0.0.2 - 127.0.0.2   10005\nAll IPs                 10007\nAll IPs                 10008\nAll IPs                 10009\n'  # noqa


def test_repair(tmp_schains_dir):
    os.mkdir(os.path.join(tmp_schains_dir, 'test-schain'))
    os.environ['TZ'] = 'Europe/London'
    time.tzset()
    payload = []
    resp_mock = response_mock(
        requests.codes.ok,
        json_data={'payload': payload, 'status': 'ok'}
    )
    result = run_command(repair, ['test-schain', '--yes'])
    assert result.output == 'Schain has been set for repair\n'
    assert result.exit_code == 0


def test_info():
    payload = {
        'name': 'attractive-ed-asich',
        'id': '0xfb3b68013fa494407b691b4b603d84c66076c0a5ac96a7d6b162d7341d74fa61',
        'owner': '0x1111111111111111111111111111111111111111',
        'part_of_node': 0, 'dkg_status': 3, 'is_deleted': False,
        'first_run': False, 'repair_mode': False
    }
    resp_mock = response_mock(
        requests.codes.ok,
        json_data={'payload': payload, 'status': 'ok'}
    )
    result = run_command_mock('node_cli.utils.helper.requests.get', resp_mock, info_,
                              ['attractive-ed-asich'])
    assert result.output == '       Name                                           Id                                                     Owner                      Part_of_node   Dkg_status   Is_deleted   First_run   Repair_mode\n--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------\nattractive-ed-asich   0xfb3b68013fa494407b691b4b603d84c66076c0a5ac96a7d6b162d7341d74fa61   0x1111111111111111111111111111111111111111   0              3            False        False       False      \n'  # noqa
    assert result.exit_code == 0

    payload = ['error']
    resp_mock = response_mock(
        requests.codes.ok,
        json_data={'payload': payload, 'status': 'error'}
    )
    result = run_command_mock('node_cli.utils.helper.requests.get', resp_mock, info_,
                              ['schain not found'])
    assert result.output == f'Command failed with following errors:\n--------------------------------------------------\nerror\n--------------------------------------------------\nYou can find more info in {G_CONF_HOME}.skale/.skale-cli-log/debug-node-cli.log\n'  # noqa
    assert result.exit_code == 3
