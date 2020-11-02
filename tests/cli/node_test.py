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
import mock
import requests
from pathlib import Path

from configs import NODE_DATA_PATH, SKALE_DIR
from cli.node import (init_node,
                      node_about, node_info, register_node, signature,
                      update_node, backup_node, restore_node,
                      set_node_in_maintenance, remove_node_from_maintenance, _turn_off, _turn_on)

from tests.helper import response_mock, run_command_mock, run_command, subprocess_run_mock
from tests.resources_test import disk_alloc_mock


def test_register_node(config):
    resp_mock = response_mock(
        requests.codes.ok,
        {'status': 'ok', 'payload': None}
    )
    result = run_command_mock(
        'core.helper.requests.post',
        resp_mock,
        register_node,
        ['--name', 'test-node', '--ip', '0.0.0.0', '--port', '8080'])
    assert result.exit_code == 0
    assert result.output == 'Node registered in SKALE manager.\nFor more info run < skale node info >\n'  # noqa


def test_register_node_with_error(config):
    resp_mock = response_mock(
        requests.codes.ok,
        {'status': 'error', 'payload': ['Strange error']},
    )
    result = run_command_mock(
        'core.helper.requests.post',
        resp_mock,
        register_node,
        ['--name', 'test-node2', '--ip', '0.0.0.0', '--port', '80'])
    assert result.exit_code == 0
    assert result.output == 'Command failed with following errors:\n--------------------------------------------------\nStrange error\n--------------------------------------------------\n'  # noqa


def test_register_node_with_prompted_ip(config):
    resp_mock = response_mock(
        requests.codes.ok,
        {'status': 'ok', 'payload': None}
    )
    result = run_command_mock(
        'core.helper.requests.post',
        resp_mock,
        register_node,
        ['--name', 'test-node', '--port', '8080'], input='0.0.0.0\n')
    assert result.exit_code == 0
    assert result.output == 'Enter node public IP: 0.0.0.0\nNode registered in SKALE manager.\nFor more info run < skale node info >\n'  # noqa


def test_register_node_with_default_port_and_name(config):
    resp_mock = response_mock(
        requests.codes.ok,
        {'status': 'ok', 'payload': None}
    )
    result = run_command_mock(
        'core.helper.requests.post',
        resp_mock,
        register_node,
        input='0.0.0.0\n')
    assert result.exit_code == 0
    assert result.output == 'Enter node public IP: 0.0.0.0\nNode registered in SKALE manager.\nFor more info run < skale node info >\n'  # noqa


def test_init_node(config):
    resp_mock = response_mock(requests.codes.created)
    with mock.patch('subprocess.run', new=subprocess_run_mock), \
            mock.patch('cli.node.install_host_dependencies'), \
            mock.patch('core.node.prepare_host'), \
            mock.patch('core.host.init_data_dir'):
        result = run_command_mock(
            'core.helper.post_request',
            resp_mock,
            init_node,
            ['./tests/test-env'])
        assert result.exit_code == 0
        assert result.output == 'Waiting for transaction manager initialization ...\nInit procedure finished\n'  # noqa


# def test_purge(config):
#     params = ['--yes']
#     resp_mock = response_mock(requests.codes.created)
#     with mock.patch('core.node.subprocess.run'):
#         result = run_command_mock(
#             'core.node.post',
#             resp_mock,
#             purge_node,
#             params
#         )
#         assert result.exit_code == 0
#         assert result.output == ''  # noqa


def test_update_node(config):
    os.makedirs(NODE_DATA_PATH, exist_ok=True)
    params = ['./tests/test-env', '--yes']
    resp_mock = response_mock(requests.codes.created)
    with mock.patch('subprocess.run', new=subprocess_run_mock), \
            mock.patch('cli.node.install_host_dependencies'), \
            mock.patch('core.node.get_flask_secret_key'), \
            mock.patch('core.node.save_env_params'), \
            mock.patch('core.node.prepare_host'), \
            mock.patch('core.resources.get_disk_alloc', new=disk_alloc_mock), \
            mock.patch('core.host.init_data_dir'):
        result = run_command_mock(
            'core.helper.post_request',
            resp_mock,
            update_node,
            params,
            input='/dev/sdp')
        assert result.exit_code == 0
        assert result.output == 'Resource allocation file was updated\nUpdating the node...\nWaiting for transaction manager initialization ...\nUpdate procedure finished\n'  # noqa


def test_update_node_without_init(config):
    params = ['./tests/test-env', '--yes']
    resp_mock = response_mock(requests.codes.created)
    with mock.patch('subprocess.run', new=subprocess_run_mock), \
            mock.patch('cli.node.install_host_dependencies'), \
            mock.patch('core.node.get_flask_secret_key'), \
            mock.patch('core.node.save_env_params'), \
            mock.patch('core.node.prepare_host'), \
            mock.patch('core.host.init_data_dir'), \
            mock.patch('core.node.is_node_inited', return_value=False):
        result = run_command_mock(
            'core.helper.post_request',
            resp_mock,
            update_node,
            params,
            input='/dev/sdp')
        assert result.exit_code == 0
        assert result.output == "Node hasn't been inited before.\nYou should run < skale node init >\n"  # noqa


def test_node_info_node_about(config):
    payload = {
        'libraries': {
            'javascript': 'N/A', 'python': '0.89.0'},
        'contracts': {
            'token': '0x3',
            'manager': '0x23'
        },
        'network': {
            'endpoint': 'ws://0.0.0.0:8080'
        },
        'local_wallet': {
            'address': '0xf',
            'eth_balance_wei': '15',
            'skale_balance_wei': '84312304',
            'eth_balance': '2.424',
            'skale_balance': '323.123'
        }
    }
    resp_mock = response_mock(
        requests.codes.ok,
        {'status': 'ok', 'payload': payload}
    )
    result = run_command_mock('core.helper.requests.get', resp_mock, node_about)
    assert result.exit_code == 0
    assert result.output == "{'libraries': {'javascript': 'N/A', 'python': '0.89.0'}, 'contracts': {'token': '0x3', 'manager': '0x23'}, 'network': {'endpoint': 'ws://0.0.0.0:8080'}, 'local_wallet': {'address': '0xf', 'eth_balance_wei': '15', 'skale_balance_wei': '84312304', 'eth_balance': '2.424', 'skale_balance': '323.123'}}\n"  # noqa


def test_node_info_node_info(config):
    payload = {
        'node_info': {
            'name': 'test', 'ip': '0.0.0.0',
            'publicIP': '1.1.1.1',
            'port': 10001,
            'publicKey': '0x7',
            'start_date': 1570114466,
            'leaving_date': 0,
            'last_reward_date': 1570628924, 'second_address': 0,
            'status': 0, 'id': 32, 'owner': '0x23'
        }
    }

    resp_mock = response_mock(
        requests.codes.ok,
        json_data={'payload': payload, 'status': 'ok'}
    )
    result = run_command_mock('core.helper.requests.get', resp_mock, node_info)
    assert result.exit_code == 0
    assert result.output == '--------------------------------------------------\nNode info\nName: test\nIP: 0.0.0.0\nPublic IP: 1.1.1.1\nPort: 10001\nStatus: Active\n--------------------------------------------------\n'  # noqa


def test_node_info_node_info_not_created(config):
    payload = {
        'node_info': {
            'name': 'test', 'ip': '0.0.0.0',
            'publicIP': '1.1.1.1',
            'port': 10001,
            'publicKey': '0x7',
            'start_date': 1570114466,
            'leaving_date': 0,
            'last_reward_date': 1570628924, 'second_address': 0,
            'status': 5, 'id': 32, 'owner': '0x23'
        }
    }

    resp_mock = response_mock(
        requests.codes.ok,
        json_data={'payload': payload, 'status': 'ok'}
    )
    result = run_command_mock('core.helper.requests.get', resp_mock, node_info)
    assert result.exit_code == 0
    assert result.output == 'This SKALE node is not registered on SKALE Manager yet\n'


def test_node_info_node_info_frozen(config):
    payload = {
        'node_info': {
            'name': 'test', 'ip': '0.0.0.0',
            'publicIP': '1.1.1.1',
            'port': 10001,
            'publicKey': '0x7',
            'start_date': 1570114466,
            'leaving_date': 0,
            'last_reward_date': 1570628924, 'second_address': 0,
            'status': 2, 'id': 32, 'owner': '0x23'
        }
    }

    resp_mock = response_mock(
        requests.codes.ok,
        json_data={'payload': payload, 'status': 'ok'}
    )
    result = run_command_mock('core.helper.requests.get', resp_mock, node_info)
    assert result.exit_code == 0
    assert result.output == '--------------------------------------------------\nNode info\nName: test\nIP: 0.0.0.0\nPublic IP: 1.1.1.1\nPort: 10001\nStatus: Frozen\n--------------------------------------------------\n'  # noqa


def test_node_info_node_info_left(config):
    payload = {
        'node_info': {
            'name': 'test', 'ip': '0.0.0.0',
            'publicIP': '1.1.1.1',
            'port': 10001,
            'publicKey': '0x7',
            'start_date': 1570114466,
            'leaving_date': 0,
            'last_reward_date': 1570628924, 'second_address': 0,
            'status': 4, 'id': 32, 'owner': '0x23'
        }
    }

    resp_mock = response_mock(
        requests.codes.ok,
        json_data={'payload': payload, 'status': 'ok'}
    )
    result = run_command_mock('core.helper.requests.get', resp_mock, node_info)
    assert result.exit_code == 0
    assert result.output == '--------------------------------------------------\nNode info\nName: test\nIP: 0.0.0.0\nPublic IP: 1.1.1.1\nPort: 10001\nStatus: Left\n--------------------------------------------------\n'  # noqa


def test_node_info_node_info_leaving(config):
    payload = {
        'node_info': {
            'name': 'test', 'ip': '0.0.0.0',
            'publicIP': '1.1.1.1',
            'port': 10001,
            'publicKey': '0x7',
            'start_date': 1570114466,
            'leaving_date': 0,
            'last_reward_date': 1570628924, 'second_address': 0,
            'status': 1, 'id': 32, 'owner': '0x23'
        }
    }

    resp_mock = response_mock(
        requests.codes.ok,
        json_data={'payload': payload, 'status': 'ok'}
    )
    result = run_command_mock('core.helper.requests.get', resp_mock, node_info)
    assert result.exit_code == 0
    assert result.output == '--------------------------------------------------\nNode info\nName: test\nIP: 0.0.0.0\nPublic IP: 1.1.1.1\nPort: 10001\nStatus: Leaving\n--------------------------------------------------\n'  # noqa


def test_node_info_node_info_in_maintenance(config):
    payload = {
        'node_info': {
            'name': 'test', 'ip': '0.0.0.0',
            'publicIP': '1.1.1.1',
            'port': 10001,
            'publicKey': '0x7',
            'start_date': 1570114466,
            'leaving_date': 0,
            'last_reward_date': 1570628924, 'second_address': 0,
            'status': 3, 'id': 32, 'owner': '0x23'
        }
    }

    resp_mock = response_mock(
        requests.codes.ok,
        json_data={'payload': payload, 'status': 'ok'}
    )
    result = run_command_mock('core.helper.requests.get', resp_mock, node_info)
    assert result.exit_code == 0
    assert result.output == '--------------------------------------------------\nNode info\nName: test\nIP: 0.0.0.0\nPublic IP: 1.1.1.1\nPort: 10001\nStatus: In Maintenance\n--------------------------------------------------\n'  # noqa


def test_node_signature():
    signature_sample = '0x1231231231'
    response_data = {
        'status': 'ok',
        'payload': {'signature': signature_sample}
    }
    resp_mock = response_mock(requests.codes.ok, json_data=response_data)
    result = run_command_mock('core.helper.requests.get',
                              resp_mock, signature, ['1'])
    assert result.exit_code == 0
    assert result.output == f'Signature: {signature_sample}\n'


def test_backup():
    Path(SKALE_DIR).mkdir(parents=True, exist_ok=True)
    with mock.patch('core.mysql_backup.run_mysql_cmd'):
        result = run_command(
            backup_node,
            [
                '/tmp',
                './tests/test-env'
            ]
        )
        assert result.exit_code == 0
        assert 'Backup archive succesfully created: /tmp/skale-node-backup-' in result.output


def test_restore():
    Path(SKALE_DIR).mkdir(parents=True, exist_ok=True)
    result = run_command(
        backup_node,
        ['/tmp']
    )
    backup_path = result.output.replace(
        'Backup archive succesfully created: ', '').replace('\n', '')
    with mock.patch('subprocess.run', new=subprocess_run_mock):
        result = run_command(
            restore_node,
            [backup_path, './tests/test-env']
        )
        assert result.exit_code == 0
        assert 'Node succesfully restored from backup\n' in result.output  # noqa


def test_maintenance_on():
    resp_mock = response_mock(
        requests.codes.ok,
        {'status': 'ok', 'payload': None}
    )
    result = run_command_mock(
        'core.helper.requests.post',
        resp_mock,
        set_node_in_maintenance,
        ['--yes'])
    assert result.exit_code == 0
    assert result.output == 'Setting maintenance mode on...\nNode is successfully set in maintenance mode\n' # noqa


def test_maintenance_off():
    resp_mock = response_mock(
        requests.codes.ok,
        {'status': 'ok', 'payload': None}
    )
    result = run_command_mock(
        'core.helper.requests.post',
        resp_mock,
        remove_node_from_maintenance)
    assert result.exit_code == 0
    assert result.output == 'Setting maintenance mode off...\nNode is successfully removed from maintenance mode\n' # noqa


def test_turn_off_maintenance_on():
    resp_mock = response_mock(
        requests.codes.ok,
        {'status': 'ok', 'payload': None}
    )
    with mock.patch('subprocess.run', new=subprocess_run_mock):
        result = run_command_mock(
            'core.helper.requests.post',
            resp_mock,
            _turn_off,
            [
                '--maintenance-on',
                '--yes'
            ])
    assert result.exit_code == 0
    assert result.output == 'Setting maintenance mode on...\nNode is successfully set in maintenance mode\nTuring off the node...\nNode was successfully turned off\n' # noqa


def test_turn_on_maintenance_off():
    resp_mock = response_mock(
        requests.codes.ok,
        {'status': 'ok', 'payload': None}
    )
    with mock.patch('subprocess.run', new=subprocess_run_mock), \
            mock.patch('core.node.get_flask_secret_key'):
        result = run_command_mock(
            'core.helper.requests.post',
            resp_mock,
            _turn_on,
            [
                './tests/test-env',
                '--maintenance-off',
                '--sync-schains',
                '--yes'
            ])

    print('result.outputresult.output result.output result.output')
    print(result.output)
    assert result.exit_code == 0
    assert result.output == 'Turning on the node...\nWaiting for transaction manager initialization ...\nNode was successfully turned on\nSetting maintenance mode off...\nNode is successfully removed from maintenance mode\n' # noqa
