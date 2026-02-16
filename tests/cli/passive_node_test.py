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

import logging
import pathlib

import mock

from node_cli.cli.passive_node import cleanup_node, _init_passive, _update_passive
from node_cli.configs import NODE_DATA_PATH, SKALE_DIR
from node_cli.core.node_options import NodeOptions
from node_cli.utils.helper import init_default_logger
from node_cli.utils.meta import CliMeta
from node_cli.utils.node_type import NodeType, NodeMode
from tests.conftest import set_env_var
from tests.helper import run_command, subprocess_run_mock
from tests.resources_test import BIG_DISK_SIZE

logger = logging.getLogger(__name__)
init_default_logger()


def test_init_passive(mocked_g_config, clean_node_options, passive_user_conf):
    pathlib.Path(SKALE_DIR).mkdir(parents=True, exist_ok=True)
    with (
        mock.patch('subprocess.run', new=subprocess_run_mock),
        mock.patch('node_cli.core.node.init_passive_op'),
        mock.patch('node_cli.core.node.is_base_containers_alive', return_value=True),
        mock.patch('node_cli.core.resources.get_disk_size', return_value=BIG_DISK_SIZE),
        mock.patch('node_cli.operations.base.configure_nftables'),
        mock.patch('node_cli.utils.decorators.is_node_inited', return_value=False),
    ):
        result = run_command(_init_passive, [passive_user_conf.as_posix()])

        node_options = NodeOptions()
        assert not node_options.archive
        assert not node_options.catchup
        assert not node_options.historic_state

        assert result.exit_code == 0


def test_init_passive_archive(mocked_g_config, clean_node_options, passive_user_conf):
    pathlib.Path(NODE_DATA_PATH).mkdir(parents=True, exist_ok=True)
    with (
        mock.patch('node_cli.core.node.is_base_containers_alive', return_value=True),
        mock.patch('node_cli.operations.base.cleanup_volume_artifacts'),
        mock.patch('node_cli.operations.base.download_skale_node'),
        mock.patch('node_cli.operations.base.sync_skale_node'),
        mock.patch('node_cli.operations.base.configure_docker'),
        mock.patch('node_cli.operations.base.prepare_host'),
        mock.patch('node_cli.operations.base.save_internal_settings'),
        mock.patch('node_cli.operations.base.run_host_checks', return_value=[]),
        mock.patch('node_cli.operations.base.ensure_filestorage_mapping'),
        mock.patch('node_cli.operations.base.generate_nginx_config'),
        mock.patch('node_cli.operations.base.get_settings'),
        mock.patch('node_cli.operations.base.prepare_block_device'),
        mock.patch('node_cli.operations.base.CliMetaManager.update_meta'),
        mock.patch('node_cli.operations.base.update_resource_allocation'),
        mock.patch('node_cli.operations.base.update_images'),
        mock.patch('node_cli.operations.base.compose_up'),
        mock.patch('node_cli.core.resources.get_disk_size', return_value=BIG_DISK_SIZE),
        mock.patch('node_cli.operations.base.configure_nftables'),
        mock.patch('node_cli.utils.decorators.is_node_inited', return_value=False),
        mock.patch('node_cli.cli.node.TYPE', NodeType.SKALE),
    ):
        result = run_command(_init_passive, [passive_user_conf.as_posix(), '--archive'])
        node_options = NodeOptions()

        assert node_options.archive
        assert node_options.catchup
        assert node_options.historic_state

        assert result.exit_code == 0


def test_init_archive_indexer_fail(mocked_g_config, clean_node_options):
    pathlib.Path(SKALE_DIR).mkdir(parents=True, exist_ok=True)
    with (
        mock.patch('subprocess.run', new=subprocess_run_mock),
        mock.patch('node_cli.core.node.init_passive_op'),
        mock.patch('node_cli.core.node.is_base_containers_alive', return_value=True),
        mock.patch('node_cli.core.resources.get_disk_size', return_value=BIG_DISK_SIZE),
        mock.patch('node_cli.operations.base.configure_nftables'),
        mock.patch('node_cli.utils.decorators.is_node_inited', return_value=False),
        mock.patch('node_cli.core.node.compose_node_env', return_value={}),
        set_env_var('ENV_TYPE', 'devnet'),
    ):
        result = run_command(_init_passive, ['./tests/test-env', '--archive', '--indexer'])
        assert result.exit_code == 1
        assert 'Cannot use both' in result.output


def test_update_passive(passive_user_conf, mocked_g_config):
    pathlib.Path(SKALE_DIR).mkdir(parents=True, exist_ok=True)

    with (
        mock.patch('subprocess.run', new=subprocess_run_mock),
        mock.patch('node_cli.core.node.update_passive_op'),
        mock.patch('node_cli.core.node.is_base_containers_alive', return_value=True),
        mock.patch('node_cli.core.resources.get_disk_size', return_value=BIG_DISK_SIZE),
        mock.patch('node_cli.operations.base.configure_nftables'),
        mock.patch('node_cli.utils.decorators.is_node_inited', return_value=True),
        mock.patch(
            'node_cli.core.node.CliMetaManager.get_meta_info',
            return_value=CliMeta(version='2.6.0', config_stream='3.0.2'),
        ),
    ):
        result = run_command(_update_passive, [passive_user_conf.as_posix(), '--yes'])
        assert result.exit_code == 0


def test_cleanup_node(mocked_g_config):
    pathlib.Path(SKALE_DIR).mkdir(parents=True, exist_ok=True)

    with (
        mock.patch('subprocess.run', new=subprocess_run_mock),
        mock.patch('node_cli.core.node.cleanup_skale_op') as cleanup_mock,
        mock.patch('node_cli.core.node.is_base_containers_alive', return_value=True),
        mock.patch('node_cli.core.resources.get_disk_size', return_value=BIG_DISK_SIZE),
        mock.patch('node_cli.operations.base.configure_nftables'),
        mock.patch('node_cli.utils.decorators.is_node_inited', return_value=True),
        mock.patch('node_cli.core.node.compose_node_env', return_value={'SCHAIN_NAME': 'test'}),
        mock.patch(
            'node_cli.core.node.CliMetaManager.get_meta_info',
            return_value=CliMeta(version='2.6.0', config_stream='3.0.2'),
        ),
    ):
        result = run_command(cleanup_node, ['--yes'])
        assert result.exit_code == 0
        cleanup_mock.assert_called_once_with(
            node_mode=NodeMode.PASSIVE, prune=False, compose_env={'SCHAIN_NAME': 'test'}
        )
