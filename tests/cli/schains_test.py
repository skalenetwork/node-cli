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
import time

import requests

from tests.helper import response_mock, run_command_mock
from cli.schains import (get_schain_config, ls, dkg, checks,
                         show_rules, turn_off_rules, turn_on_rules)


def test_ls(config):
    os.environ['TZ'] = 'Europe/London'
    time.tzset()
    payload = [
        {
            'name': 'test_schain1', 'owner': '0x123',
            'indexInOwnerList': 3, 'partOfNode': 0,
            'lifetime': 5, 'startDate': 1570115385,
            'deposit': 1000000000000000000, 'index': 3
        },
        {
            'name': 'crazy_cats1',
            'owner': '0x321',
            'indexInOwnerList': 8, 'partOfNode': 0,
            'lifetime': 5, 'startDate': 1570469410,
            'deposit': 1000000000000000000, 'index': 8
        }
    ]
    resp_mock = response_mock(
        requests.codes.ok,
        json_data={'payload': payload, 'status': 'ok'}
    )
    result = run_command_mock('core.helper.requests.get', resp_mock, ls)
    assert result.exit_code == 0
    assert result.output == '    Name       Owner   Size   Lifetime        Created At              Deposit      \n-----------------------------------------------------------------------------------\ntest_schain1   0x123   0      5          Oct 03 2019 16:09:45   1000000000000000000\ncrazy_cats1    0x321   0      5          Oct 07 2019 18:30:10   1000000000000000000\n'  # noqa


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
    result = run_command_mock('core.helper.requests.get',
                              resp_mock, dkg)
    print(result)
    assert result.exit_code == 0
    assert result.output == '  sChain Name      DKG Status          Added At         sChain Status\n---------------------------------------------------------------------\nmelodic-aldhibah   IN_PROGRESS   Jan 08 2020 15:26:52   Active       \n'  # noqa

    result = run_command_mock('core.helper.requests.get',
                              resp_mock, dkg, ['--all'])
    print(result)
    assert result.exit_code == 0
    assert result.output == '  sChain Name      DKG Status          Added At         sChain Status\n---------------------------------------------------------------------\nmelodic-aldhibah   IN_PROGRESS   Jan 08 2020 15:26:52   Active       \n'  # noqa


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
    result = run_command_mock('core.helper.requests.get',
                              resp_mock,
                              get_schain_config, ['test1'])
    assert result.exit_code == 0
    assert result.output == "{'nodeInfo': {'basePort': 10011,\n              'bindIP': '123.123.123.123',\n              'httpRpcPort': 10009,\n              'httpsRpcPort': 11118,\n              'nodeID': 2,\n              'nodeName': 'testnet-1',\n              'wsRpcPort': 10118,\n              'wssRpcPort': 13219},\n 'sChain': {'nodes': [{'basePort': 10011,\n                       'httpRpcPort': 10013,\n                       'httpsRpcPort': 10018,\n                       'ip': '213.13.123.13',\n                       'nodeID': 2,\n                       'nodeName': 'testnet-1',\n                       'owner': '0xe3213',\n                       'publicIP': '1.1.1.1',\n                       'publicKey': 'public_key',\n                       'schainIndex': 1,\n                       'wsRpcPort': 10014,\n                       'wssRpcPort': 10019},\n                      {'basePort': 10077,\n                       'httpRpcPort': 10079,\n                       'httpsRpcPort': 10084,\n                       'ip': '2.2.2.2',\n                       'nodeID': 0,\n                       'nodeName': 'testnet-2',\n                       'owner': '0x323',\n                       'publicIP': '3.3.3.3',\n                       'publicKey': 'public_key352',\n                       'schainIndex': 2,\n                       'wsRpcPort': 10080,\n                       'wssRpcPort': 10085}],\n            'schainID': 1,\n            'schainName': 'test1'}}\n"  # noqa


def test_schain_rules():
    payload = {
        'endpoints': [
            {'ip': '127.0.0.1', 'port': 10000},
            {'ip': '127.0.0.1', 'port': 10001},
            {'ip': '127.0.0.1', 'port': 10004},
            {'ip': '127.0.0.1', 'port': 10005},
            {'ip': None, 'port': 10003},
            {'ip': None, 'port': 10002},
            {'ip': None, 'port': 10008},
            {'ip': None, 'port': 10007}
        ]
    }
    resp_mock = response_mock(
        requests.codes.ok,
        json_data={'payload': payload, 'status': 'ok'}
    )
    result = run_command_mock(
        'core.helper.requests.get', resp_mock, show_rules, ['schain-test'])
    assert result.exit_code == 0
    print(repr(result.output))
    assert result.output == 'Port       Ip    \n-----------------\n10000   127.0.0.1\n10001   127.0.0.1\n10002   None     \n10003   None     \n10004   127.0.0.1\n10005   127.0.0.1\n10007   None     \n10008   None     \n'  # noqa


def test_turn_on_schain_rules():
    resp_mock = response_mock(
        requests.codes.ok,
        json_data={'payload': [], 'status': 'ok'}
    )
    result = run_command_mock(
        'core.helper.requests.post', resp_mock,
        turn_on_rules, ['schain-test'])
    assert result.exit_code == 0
    assert result.output == 'Success\n'


def test_turn_off_schain_rules():
    resp_mock = response_mock(
        requests.codes.ok,
        json_data={'payload': [], 'status': 'ok'}
    )
    result = run_command_mock(
        'core.helper.requests.post', resp_mock,
        turn_off_rules, ['schain-test', '--yes'])
    assert result.exit_code == 0
    assert result.output == 'WARNING: Closing endpoints for schain. Ctrl-C to abort\nSuccess\n'


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
                "firewall_rules": False
            }
        }
    ]
    resp_mock = response_mock(
        requests.codes.ok,
        json_data={'payload': payload, 'status': 'ok'}
    )
    result = run_command_mock('core.helper.requests.get',
                              resp_mock, checks)

    assert result.exit_code == 0
    assert result.output == 'sChain Name   Data directory    DKG    Config file   Volume   Container    IMA    Firewall\n------------------------------------------------------------------------------------------\ntest_schain   True             False   False         False    False       False   False   \n'  # noqa

    result = run_command_mock('core.helper.requests.get',
                              resp_mock, checks, ['--json'])

    assert result.exit_code == 0
    assert result.output == '[{"name": "test_schain", "healthchecks": {"data_dir": true, "dkg": false, "config": false, "volume": false, "container": false, "ima_container": false, "firewall_rules": false}}]\n'  # noqa
