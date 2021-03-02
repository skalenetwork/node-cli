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
import json
import mock
import requests

import pytest

from core.host import safe_mk_dirs
from configs.resource_allocation import (
    RESOURCE_ALLOCATION_FILEPATH, NODE_DATA_PATH
)
from tools.helper import write_json
from tests.resources_test import disk_alloc_mock
from tests.helper import response_mock, run_command_mock

from cli.resources_allocation import show, generate


TEST_CONFIG = {'test': 1}


def check_node_dir():
    if not os.path.exists(NODE_DATA_PATH):
        safe_mk_dirs(NODE_DATA_PATH)


@pytest.fixture
def resource_alloc_config():
    write_json(RESOURCE_ALLOCATION_FILEPATH, TEST_CONFIG)
    yield RESOURCE_ALLOCATION_FILEPATH
    os.remove(RESOURCE_ALLOCATION_FILEPATH)


def test_show(config, resource_alloc_config):
    check_node_dir()
    resp_mock = response_mock(requests.codes.created)
    write_json(RESOURCE_ALLOCATION_FILEPATH, TEST_CONFIG)
    result = run_command_mock(
        'core.helper.post_request',
        resp_mock,
        show
    )
    assert result.output == json.dumps(TEST_CONFIG, indent=4) + '\n'
    assert result.exit_code == 0


def test_generate():
    check_node_dir()
    resp_mock = response_mock(requests.codes.created)
    with mock.patch('core.resources.get_static_disk_alloc',
                    new=disk_alloc_mock):
        result = run_command_mock(
            'core.helper.post_request',
            resp_mock,
            generate,
            ['./tests/test-env', '--yes']
        )
    assert result.output == (f'Resource allocation file generated: '
                             f'{RESOURCE_ALLOCATION_FILEPATH}\n')
    assert result.exit_code == 0


def test_generate_already_exists(resource_alloc_config):
    check_node_dir()
    resp_mock = response_mock(requests.codes.created)
    with mock.patch('core.resources.get_static_disk_alloc',
                    new=disk_alloc_mock):
        result = run_command_mock(
            'core.helper.post_request',
            resp_mock,
            generate,
            ['./tests/test-env', '--yes']
        )
        assert result.output == 'Resource allocation file is already exists\n'
        assert result.exit_code == 0

        result = run_command_mock(
                'core.helper.post_request',
                resp_mock,
                generate,
                ['./tests/test-env', '--yes', '--force']
        )
        assert result.output == (
            f'Resource allocation file generated: '
            f'{RESOURCE_ALLOCATION_FILEPATH}\n'
        )
        assert result.exit_code == 0
