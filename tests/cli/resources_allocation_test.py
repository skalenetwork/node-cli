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

from node_cli.configs.resource_allocation import (
    RESOURCE_ALLOCATION_FILEPATH, NODE_DATA_PATH
)
from node_cli.utils.helper import safe_mkdir, write_json
from tests.helper import response_mock, run_command_mock

from node_cli.cli.resources_allocation import show, generate

from tests.resources_test import BIG_DISK_SIZE


TEST_CONFIG = {'test': 1}


@pytest.fixture
def resource_alloc_config():
    write_json(RESOURCE_ALLOCATION_FILEPATH, TEST_CONFIG)
    yield RESOURCE_ALLOCATION_FILEPATH
    os.remove(RESOURCE_ALLOCATION_FILEPATH)


def test_show(resource_alloc_config):
    resp_mock = response_mock(requests.codes.created)
    write_json(RESOURCE_ALLOCATION_FILEPATH, TEST_CONFIG)
    result = run_command_mock(
        'node_cli.utils.helper.post_request',
        resp_mock,
        show
    )
    assert result.output == json.dumps(TEST_CONFIG, indent=4) + '\n'
    assert result.exit_code == 0


def test_generate():
    safe_mkdir(NODE_DATA_PATH)
    resp_mock = response_mock(requests.codes.created)
    with mock.patch('node_cli.core.resources.get_disk_size',
                    return_value=BIG_DISK_SIZE):
        result = run_command_mock(
            'node_cli.utils.helper.post_request',
            resp_mock,
            generate,
            ['./tests/test-env', '--yes']
        )
    assert result.output == (f'Resource allocation file generated: '
                             f'{RESOURCE_ALLOCATION_FILEPATH}\n')
    assert result.exit_code == 0


def test_generate_already_exists(resource_alloc_config):
    resp_mock = response_mock(requests.codes.created)
    with mock.patch('node_cli.core.resources.get_disk_size',
                    return_value=BIG_DISK_SIZE):
        result = run_command_mock(
            'node_cli.utils.helper.post_request',
            resp_mock,
            generate,
            ['./tests/test-env', '--yes']
        )
        assert result.output == 'Resource allocation file is already exists\n'
        assert result.exit_code == 0

        result = run_command_mock(
                'node_cli.utils.helper.post_request',
                resp_mock,
                generate,
                ['./tests/test-env', '--yes', '--force']
        )
        assert result.output == (
            f'Resource allocation file generated: '
            f'{RESOURCE_ALLOCATION_FILEPATH}\n'
        )
        assert result.exit_code == 0
