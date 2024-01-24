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

from node_cli.configs import SKALE_DIR, NODE_DATA_PATH
from node_cli.cli.sync_node import _init_sync, _update_sync
from node_cli.utils.helper import init_default_logger
from node_cli.core.node_options import NodeOptions

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


def test_init_sync_archive_catchup(mocked_g_config, clean_node_options):
    pathlib.Path(NODE_DATA_PATH).mkdir(parents=True, exist_ok=True)
#     with mock.patch('subprocess.run', new=subprocess_run_mock), \
    with mock.patch('node_cli.core.node.is_base_containers_alive', return_value=True), \
            mock.patch('node_cli.operations.base.cleanup_volume_artifacts'), \
            mock.patch('node_cli.operations.base.download_skale_node'), \
            mock.patch('node_cli.operations.base.sync_skale_node'), \
            mock.patch('node_cli.operations.base.configure_docker'), \
            mock.patch('node_cli.operations.base.prepare_host'), \
            mock.patch('node_cli.operations.base.ensure_filestorage_mapping'), \
            mock.patch('node_cli.operations.base.link_env_file'), \
            mock.patch('node_cli.operations.base.download_contracts'), \
            mock.patch('node_cli.operations.base.generate_nginx_config'), \
            mock.patch('node_cli.operations.base.prepare_block_device'), \
            mock.patch('node_cli.operations.base.update_meta'), \
            mock.patch('node_cli.operations.base.update_resource_allocation'), \
            mock.patch('node_cli.operations.base.update_images'), \
            mock.patch('node_cli.operations.base.compose_up_sync'), \
            mock.patch('node_cli.core.resources.get_disk_size', return_value=BIG_DISK_SIZE), \
            mock.patch('node_cli.core.node.configure_firewall_rules'), \
            mock.patch('node_cli.utils.decorators.is_node_inited', return_value=False):
        result = run_command(
            _init_sync,
            ['./tests/test-env', '--archive', '--catchup', '--historic-state']
        )
        node_options = NodeOptions()

        assert node_options.archive
        assert node_options.catchup
        assert node_options.historic_state

        assert result.exit_code == 0


def test_init_sync_historic_state_fail(mocked_g_config, clean_node_options):
    pathlib.Path(SKALE_DIR).mkdir(parents=True, exist_ok=True)
    with mock.patch('subprocess.run', new=subprocess_run_mock), \
            mock.patch('node_cli.core.node.init_sync_op'), \
            mock.patch('node_cli.core.node.is_base_containers_alive', return_value=True), \
            mock.patch('node_cli.core.resources.get_disk_size', return_value=BIG_DISK_SIZE), \
            mock.patch('node_cli.core.node.configure_firewall_rules'), \
            mock.patch('node_cli.utils.decorators.is_node_inited', return_value=False):
        result = run_command(
            _init_sync,
            ['./tests/test-env', '--historic-state']
        )
        assert result.exit_code == 1
        assert '--historic-state can be used only' in result.output


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
