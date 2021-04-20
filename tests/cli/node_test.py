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
from pathlib import Path

import mock
import requests
import logging

from node_cli.configs import NODE_DATA_PATH, SKALE_DIR
from node_cli.core.resources import ResourceAlloc
from node_cli.cli.node import (init_node, node_info, register_node, signature,
                               update_node, backup_node, restore_node,
                               set_node_in_maintenance,
                               remove_node_from_maintenance, _turn_off, _turn_on, _set_domain_name)
from node_cli.utils.helper import init_default_logger

from tests.helper import (
    response_mock, run_command_mock,
    run_command, subprocess_run_mock
)

logger = logging.getLogger(__name__)
init_default_logger()


def disk_alloc_mock(env_type):
    return ResourceAlloc(128)


def test_register_node(mocked_g_config):
    resp_mock = response_mock(
        requests.codes.ok,
        {'status': 'ok', 'payload': None}
    )
    with mock.patch('node_cli.utils.decorators.is_node_inited', return_value=True):
        result = run_command_mock(
            'node_cli.utils.helper.requests.post',
            resp_mock,
            register_node,
            ['--name', 'test-node', '--ip', '0.0.0.0', '--port', '8080', '-d', 'skale.test'])
    assert result.exit_code == 0
    assert result.output == 'Node registered in SKALE manager.\nFor more info run < skale node info >\n'  # noqa


def test_register_node_with_error(mocked_g_config):
    resp_mock = response_mock(
        requests.codes.ok,
        {'status': 'error', 'payload': ['Strange error']},
    )
    with mock.patch('node_cli.utils.decorators.is_node_inited', return_value=True):
        result = run_command_mock(
            'node_cli.utils.helper.requests.post',
            resp_mock,
            register_node,
            ['--name', 'test-node2', '--ip', '0.0.0.0', '--port', '80', '-d', 'skale.test'])
    assert result.exit_code == 3
    assert result.output == 'Command failed with following errors:\n--------------------------------------------------\nStrange error\n--------------------------------------------------\nYou can find more info in tests/.skale/.skale-cli-log/debug-node-cli.log\n'  # noqa


def test_register_node_with_prompted_ip(mocked_g_config):
    resp_mock = response_mock(
        requests.codes.ok,
        {'status': 'ok', 'payload': None}
    )
    with mock.patch('node_cli.utils.decorators.is_node_inited', return_value=True):
        result = run_command_mock(
            'node_cli.utils.helper.requests.post',
            resp_mock,
            register_node,
            ['--name', 'test-node', '--port', '8080', '-d', 'skale.test'], input='0.0.0.0\n')
    assert result.exit_code == 0
    assert result.output == 'Enter node public IP: 0.0.0.0\nNode registered in SKALE manager.\nFor more info run < skale node info >\n'  # noqa


def test_register_node_with_default_port(mocked_g_config):
    resp_mock = response_mock(
        requests.codes.ok,
        {'status': 'ok', 'payload': None}
    )
    with mock.patch('node_cli.utils.decorators.is_node_inited', return_value=True):
        result = run_command_mock(
            'node_cli.utils.helper.requests.post',
            resp_mock,
            register_node,
            ['--name', 'test-node', '-d', 'skale.test'], input='0.0.0.0\n')
    assert result.exit_code == 0
    assert result.output == 'Enter node public IP: 0.0.0.0\nNode registered in SKALE manager.\nFor more info run < skale node info >\n'  # noqa


def test_init_node(caplog):  # todo: write new init node test
    resp_mock = response_mock(requests.codes.created)
    with caplog.at_level(logging.INFO):
        with mock.patch('subprocess.run', new=subprocess_run_mock), \
                mock.patch('node_cli.core.resources.get_static_disk_alloc', new=disk_alloc_mock), \
                mock.patch('node_cli.core.host.prepare_host'), \
                mock.patch('node_cli.core.host.init_data_dir'), \
                mock.patch('node_cli.core.node.init_op'), \
                mock.patch('node_cli.core.node.is_base_containers_alive',
                           return_value=True), \
                mock.patch('node_cli.utils.decorators.is_node_inited', return_value=False):
            result = run_command_mock(
                'node_cli.utils.helper.post_request',
                resp_mock,
                init_node,
                ['./tests/test-env'])
            assert 'Init procedure finished' in caplog.text
            assert result.exit_code == 0


def test_update_node(mocked_g_config):
    os.makedirs(NODE_DATA_PATH, exist_ok=True)
    params = ['./tests/test-env', '--yes']
    resp_mock = response_mock(requests.codes.created)
    with mock.patch('subprocess.run', new=subprocess_run_mock), \
            mock.patch('node_cli.core.node.update_op'), \
            mock.patch('node_cli.core.node.get_flask_secret_key'), \
            mock.patch('node_cli.core.node.save_env_params'), \
            mock.patch('node_cli.core.host.prepare_host'), \
            mock.patch('node_cli.core.node.is_base_containers_alive',
                       return_value=True), \
            mock.patch('node_cli.core.resources.get_static_disk_alloc', new=disk_alloc_mock), \
            mock.patch('node_cli.core.host.init_data_dir'):
        result = run_command_mock(
            'node_cli.utils.helper.post_request',
            resp_mock,
            update_node,
            params,
            input='/dev/sdp')
        assert result.exit_code == 0
        # assert result.output == 'Updating the node...\nWaiting for transaction manager initialization ...\nUpdate procedure finished\n'  # noqa


def test_update_node_without_init():
    params = ['./tests/test-env', '--yes']
    resp_mock = response_mock(requests.codes.created)
    with mock.patch('subprocess.run', new=subprocess_run_mock), \
            mock.patch('node_cli.core.node.get_flask_secret_key'), \
            mock.patch('node_cli.core.node.save_env_params'), \
            mock.patch('node_cli.core.host.prepare_host'), \
            mock.patch('node_cli.core.host.init_data_dir'), \
            mock.patch('node_cli.core.node.is_base_containers_alive',
                       return_value=True), \
            mock.patch('node_cli.utils.decorators.is_node_inited', return_value=False):
        result = run_command_mock(
            'node_cli.utils.helper.post_request',
            resp_mock,
            update_node,
            params,
            input='/dev/sdp')
        assert result.exit_code == 8
        assert result.output == "Command failed with following errors:\n--------------------------------------------------\nNode hasn't been inited before.\nYou should run < skale node init >\n--------------------------------------------------\nYou can find more info in tests/.skale/.skale-cli-log/debug-node-cli.log\n"  # noqa


def test_node_info_node_info():
    payload = {
        'node_info': {
            'name': 'test', 'ip': '0.0.0.0',
            'publicIP': '1.1.1.1',
            'port': 10001,
            'publicKey': '0x7',
            'start_date': 1570114466,
            'leaving_date': 0,
            'last_reward_date': 1570628924, 'second_address': 0,
            'status': 0, 'id': 32, 'owner': '0x23',
            'domain_name': 'skale.test'
        }
    }

    resp_mock = response_mock(
        requests.codes.ok,
        json_data={'payload': payload, 'status': 'ok'}
    )
    result = run_command_mock('node_cli.utils.helper.requests.get', resp_mock, node_info)
    assert result.exit_code == 0
    assert result.output == '--------------------------------------------------\nNode info\nName: test\nID: 32\nIP: 0.0.0.0\nPublic IP: 1.1.1.1\nPort: 10001\nDomain name: skale.test\nStatus: Active\n--------------------------------------------------\n'  # noqa


def test_node_info_node_info_not_created():
    payload = {
        'node_info': {
            'name': 'test', 'ip': '0.0.0.0',
            'publicIP': '1.1.1.1',
            'port': 10001,
            'publicKey': '0x7',
            'start_date': 1570114466,
            'leaving_date': 0,
            'last_reward_date': 1570628924, 'second_address': 0,
            'status': 5, 'id': 32, 'owner': '0x23',
            'domain_name': 'skale.test'
        }
    }

    resp_mock = response_mock(
        requests.codes.ok,
        json_data={'payload': payload, 'status': 'ok'}
    )
    result = run_command_mock('node_cli.utils.helper.requests.get', resp_mock, node_info)
    assert result.exit_code == 0
    assert result.output == 'This SKALE node is not registered on SKALE Manager yet\n'


def test_node_info_node_info_frozen():
    payload = {
        'node_info': {
            'name': 'test', 'ip': '0.0.0.0',
            'publicIP': '1.1.1.1',
            'port': 10001,
            'publicKey': '0x7',
            'start_date': 1570114466,
            'leaving_date': 0,
            'last_reward_date': 1570628924, 'second_address': 0,
            'status': 2, 'id': 32, 'owner': '0x23',
            'domain_name': 'skale.test'
        }
    }

    resp_mock = response_mock(
        requests.codes.ok,
        json_data={'payload': payload, 'status': 'ok'}
    )
    result = run_command_mock('node_cli.utils.helper.requests.get', resp_mock, node_info)
    assert result.exit_code == 0
    assert result.output == '--------------------------------------------------\nNode info\nName: test\nID: 32\nIP: 0.0.0.0\nPublic IP: 1.1.1.1\nPort: 10001\nDomain name: skale.test\nStatus: Frozen\n--------------------------------------------------\n'  # noqa


def test_node_info_node_info_left():
    payload = {
        'node_info': {
            'name': 'test', 'ip': '0.0.0.0',
            'publicIP': '1.1.1.1',
            'port': 10001,
            'publicKey': '0x7',
            'start_date': 1570114466,
            'leaving_date': 0,
            'last_reward_date': 1570628924, 'second_address': 0,
            'status': 4, 'id': 32, 'owner': '0x23',
            'domain_name': 'skale.test'
        }
    }

    resp_mock = response_mock(
        requests.codes.ok,
        json_data={'payload': payload, 'status': 'ok'}
    )
    result = run_command_mock('node_cli.utils.helper.requests.get', resp_mock, node_info)
    assert result.exit_code == 0
    assert result.output == '--------------------------------------------------\nNode info\nName: test\nID: 32\nIP: 0.0.0.0\nPublic IP: 1.1.1.1\nPort: 10001\nDomain name: skale.test\nStatus: Left\n--------------------------------------------------\n'  # noqa


def test_node_info_node_info_leaving():
    payload = {
        'node_info': {
            'name': 'test', 'ip': '0.0.0.0',
            'publicIP': '1.1.1.1',
            'port': 10001,
            'publicKey': '0x7',
            'start_date': 1570114466,
            'leaving_date': 0,
            'last_reward_date': 1570628924, 'second_address': 0,
            'status': 1, 'id': 32, 'owner': '0x23',
            'domain_name': 'skale.test'
        }
    }

    resp_mock = response_mock(
        requests.codes.ok,
        json_data={'payload': payload, 'status': 'ok'}
    )
    result = run_command_mock('node_cli.utils.helper.requests.get', resp_mock, node_info)
    assert result.exit_code == 0
    assert result.output == '--------------------------------------------------\nNode info\nName: test\nID: 32\nIP: 0.0.0.0\nPublic IP: 1.1.1.1\nPort: 10001\nDomain name: skale.test\nStatus: Leaving\n--------------------------------------------------\n'  # noqa


def test_node_info_node_info_in_maintenance():
    payload = {
        'node_info': {
            'name': 'test', 'ip': '0.0.0.0',
            'publicIP': '1.1.1.1',
            'port': 10001,
            'publicKey': '0x7',
            'start_date': 1570114466,
            'leaving_date': 0,
            'last_reward_date': 1570628924, 'second_address': 0,
            'status': 3, 'id': 32, 'owner': '0x23',
            'domain_name': 'skale.test'
        }
    }

    resp_mock = response_mock(
        requests.codes.ok,
        json_data={'payload': payload, 'status': 'ok'}
    )
    result = run_command_mock('node_cli.utils.helper.requests.get', resp_mock, node_info)
    assert result.exit_code == 0
    assert result.output == '--------------------------------------------------\nNode info\nName: test\nID: 32\nIP: 0.0.0.0\nPublic IP: 1.1.1.1\nPort: 10001\nDomain name: skale.test\nStatus: In Maintenance\n--------------------------------------------------\n'  # noqa


def test_node_signature():
    signature_sample = '0x1231231231'
    response_data = {
        'status': 'ok',
        'payload': {'signature': signature_sample}
    }
    resp_mock = response_mock(requests.codes.ok, json_data=response_data)
    result = run_command_mock('node_cli.utils.helper.requests.get',
                              resp_mock, signature, ['1'])
    assert result.exit_code == 0
    assert result.output == f'Signature: {signature_sample}\n'


def test_backup():
    Path(SKALE_DIR).mkdir(parents=True, exist_ok=True)
    with mock.patch('node_cli.core.mysql_backup.run_mysql_cmd'):
        result = run_command(
            backup_node,
            [
                '/tmp',
                './tests/test-env'
            ]
        )
        assert result.exit_code == 0
        assert 'Backup archive successfully created: /tmp/skale-node-backup-' in result.output


def test_restore(mocked_g_config):
    Path(SKALE_DIR).mkdir(parents=True, exist_ok=True)
    result = run_command(
        backup_node,
        ['/tmp']
    )
    backup_path = result.output.replace(
        'Backup archive successfully created: ', '').replace('\n', '')
    with mock.patch('subprocess.run', new=subprocess_run_mock), \
            mock.patch('node_cli.core.node.restore_op'), \
            mock.patch('node_cli.core.node.restore_mysql_backup'), \
            mock.patch('node_cli.core.resources.get_static_disk_alloc', new=disk_alloc_mock), \
            mock.patch('node_cli.utils.decorators.is_node_inited', return_value=False):
        result = run_command(
            restore_node,
            [backup_path, './tests/test-env']
        )
        assert result.exit_code == 0
        assert 'Node is restored from backup\n' in result.output  # noqa


def test_maintenance_on():
    resp_mock = response_mock(
        requests.codes.ok,
        {'status': 'ok', 'payload': None}
    )
    result = run_command_mock(
        'node_cli.utils.helper.requests.post',
        resp_mock,
        set_node_in_maintenance,
        ['--yes'])
    assert result.exit_code == 0
    assert result.output == 'Setting maintenance mode on...\nNode is successfully set in maintenance mode\n'  # noqa


def test_maintenance_off(mocked_g_config):
    resp_mock = response_mock(
        requests.codes.ok,
        {'status': 'ok', 'payload': None}
    )
    result = run_command_mock(
        'node_cli.utils.helper.requests.post',
        resp_mock,
        remove_node_from_maintenance)
    assert result.exit_code == 0
    assert result.output == 'Setting maintenance mode off...\nNode is successfully removed from maintenance mode\n'  # noqa


def test_turn_off_maintenance_on(mocked_g_config):
    resp_mock = response_mock(
        requests.codes.ok,
        {'status': 'ok', 'payload': None}
    )
    with mock.patch('subprocess.run', new=subprocess_run_mock), \
            mock.patch('node_cli.core.node.turn_off_op'), \
            mock.patch('node_cli.core.node.is_node_inited', return_value=True):
        result = run_command_mock(
            'node_cli.utils.helper.requests.post',
            resp_mock,
            _turn_off,
            [
                '--maintenance-on',
                '--yes'
            ])
    assert result.exit_code == 0
    assert result.output == 'Setting maintenance mode on...\nNode is successfully set in maintenance mode\n'  # noqa


def test_turn_on_maintenance_off(mocked_g_config):
    resp_mock = response_mock(
        requests.codes.ok,
        {'status': 'ok', 'payload': None}
    )
    with mock.patch('subprocess.run', new=subprocess_run_mock), \
            mock.patch('node_cli.core.node.get_flask_secret_key'), \
            mock.patch('node_cli.core.node.turn_on_op'), \
            mock.patch('node_cli.core.node.is_base_containers_alive'), \
            mock.patch('node_cli.core.node.is_node_inited', return_value=True):
        result = run_command_mock(
            'node_cli.utils.helper.requests.post',
            resp_mock,
            _turn_on,
            [
                './tests/test-env',
                '--maintenance-off',
                '--sync-schains',
                '--yes'
            ])

    assert result.exit_code == 0
    assert result.output == 'Setting maintenance mode off...\nNode is successfully removed from maintenance mode\n'  # noqa, tmp fix


def test_set_domain_name():
    resp_mock = response_mock(
        requests.codes.ok,
        {'status': 'ok', 'payload': None}
    )

    with mock.patch('node_cli.utils.decorators.is_node_inited', return_value=True):
        result = run_command_mock(
            'node_cli.utils.helper.requests.post',
            resp_mock,
            _set_domain_name, ['-d', 'skale.test', '--yes'])
    assert result.exit_code == 0
    assert result.output == 'Setting new domain name: skale.test\nDomain name successfully changed\n'  # noqa
