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

import pathlib

import mock
import logging

from node_cli.configs import SKALE_DIR
from node_cli.cli.sync_node import _init_sync, _update_sync
from node_cli.utils.helper import init_default_logger

from tests.helper import (
    run_command, subprocess_run_mock
)
from tests.resources_test import BIG_DISK_SIZE

logger = logging.getLogger(__name__)
init_default_logger()


def test_init_sync(mocked_g_config):
    pathlib.Path(SKALE_DIR).mkdir(parents=True, exist_ok=True)
    with mock.patch('subprocess.run', new=subprocess_run_mock), \
            mock.patch('node_cli.core.node.init_sync_op'), \
            mock.patch('node_cli.core.node.is_base_containers_alive', return_value=True), \
            mock.patch('node_cli.core.resources.get_disk_size', return_value=BIG_DISK_SIZE), \
            mock.patch('node_cli.core.node.configure_firewall_rules'), \
            mock.patch('node_cli.utils.decorators.is_node_inited', return_value=False):
        result = run_command(
            _init_sync,
            ['./tests/test-env']
        )
        assert result.exit_code == 0


def test_update_sync(mocked_g_config):
    pathlib.Path(SKALE_DIR).mkdir(parents=True, exist_ok=True)
    with mock.patch('subprocess.run', new=subprocess_run_mock), \
            mock.patch('node_cli.core.node.update_sync_op'), \
            mock.patch('node_cli.core.node.is_base_containers_alive', return_value=True), \
            mock.patch('node_cli.core.resources.get_disk_size', return_value=BIG_DISK_SIZE), \
            mock.patch('node_cli.core.node.configure_firewall_rules'), \
            mock.patch('node_cli.utils.decorators.is_node_inited', return_value=True):
        result = run_command(
            _update_sync,
            ['./tests/test-env', '--yes']
        )
        assert result.exit_code == 0
