import logging
import pathlib

import mock

from node_cli.cli.passive_fair_node import cleanup_node, init_passive_node, update_node
from node_cli.configs import NODE_DATA_PATH, SKALE_DIR
from node_cli.utils.helper import init_default_logger
from node_cli.utils.meta import CliMeta
from node_cli.utils.node_type import NodeMode
from tests.helper import run_command, subprocess_run_mock
from tests.resources_test import BIG_DISK_SIZE

logger = logging.getLogger(__name__)
init_default_logger()


def test_init_fair_passive(mocked_g_config, tmp_path):
    env_file = tmp_path / 'test-env'
    env_file.write_text('')
    pathlib.Path(SKALE_DIR).mkdir(parents=True, exist_ok=True)
    with (
        mock.patch('subprocess.run', new=subprocess_run_mock),
        mock.patch('node_cli.fair.common.init_fair_op', return_value=True),
        mock.patch('node_cli.fair.common.compose_node_env', return_value={}),
        mock.patch('node_cli.fair.common.save_env_params'),
        mock.patch('node_cli.fair.passive.setup_fair_passive'),
        mock.patch('node_cli.fair.common.time.sleep'),
        mock.patch('node_cli.core.node.is_base_containers_alive', return_value=True),
        mock.patch('node_cli.core.resources.get_disk_size', return_value=BIG_DISK_SIZE),
        mock.patch('node_cli.operations.base.configure_nftables'),
        mock.patch('node_cli.utils.decorators.is_node_inited', return_value=False),
    ):
        result = run_command(
            init_passive_node,
            [
                env_file.as_posix(),
                '--id',
                '1',
            ],
        )
        assert result.exit_code == 0


def test_init_fair_passive_snapshot_any(mocked_g_config, tmp_path):
    env_file = tmp_path / 'test-env'
    env_file.write_text('')
    pathlib.Path(SKALE_DIR).mkdir(parents=True, exist_ok=True)
    with (
        mock.patch('subprocess.run', new=subprocess_run_mock),
        mock.patch('node_cli.fair.common.init_fair_op', return_value=True),
        mock.patch('node_cli.fair.common.compose_node_env', return_value={}),
        mock.patch('node_cli.fair.common.save_env_params'),
        mock.patch('node_cli.fair.passive.setup_fair_passive'),
        mock.patch('node_cli.fair.common.time.sleep'),
        mock.patch('node_cli.core.node.is_base_containers_alive', return_value=True),
        mock.patch('node_cli.core.resources.get_disk_size', return_value=BIG_DISK_SIZE),
        mock.patch('node_cli.operations.base.configure_nftables'),
        mock.patch('node_cli.utils.decorators.is_node_inited', return_value=False),
    ):
        result = run_command(
            init_passive_node,
            [
                env_file.as_posix(),
                '--id',
                '2',
                '--snapshot',
                'any',
            ],
        )
        assert result.exit_code == 0


def test_update_fair_passive(mocked_g_config, tmp_path):
    env_file = tmp_path / 'test-env'
    env_file.write_text('')
    pathlib.Path(NODE_DATA_PATH).mkdir(parents=True, exist_ok=True)
    with (
        mock.patch('subprocess.run', new=subprocess_run_mock),
        mock.patch('node_cli.fair.common.update_fair_op', return_value=True),
        mock.patch('node_cli.fair.common.compose_node_env', return_value={}),
        mock.patch('node_cli.core.node.is_base_containers_alive', return_value=True),
        mock.patch('node_cli.core.resources.get_disk_size', return_value=BIG_DISK_SIZE),
        mock.patch('node_cli.operations.base.configure_nftables'),
        mock.patch('node_cli.utils.decorators.is_node_inited', return_value=True),
    ):
        result = run_command(update_node, [env_file.as_posix(), '--yes'])
        assert result.exit_code == 0


def test_cleanup_node(mocked_g_config):
    pathlib.Path(SKALE_DIR).mkdir(parents=True, exist_ok=True)

    with (
        mock.patch('subprocess.run', new=subprocess_run_mock),
        mock.patch('node_cli.fair.common.cleanup_fair_op') as cleanup_mock,
        mock.patch('node_cli.core.node.is_base_containers_alive', return_value=True),
        mock.patch('node_cli.core.resources.get_disk_size', return_value=BIG_DISK_SIZE),
        mock.patch('node_cli.operations.base.configure_nftables'),
        mock.patch('node_cli.utils.decorators.is_node_inited', return_value=True),
        mock.patch('node_cli.fair.common.compose_node_env', return_value={'SCHAIN_NAME': 'test'}),
        mock.patch(
            'node_cli.core.node.CliMetaManager.get_meta_info',
            return_value=CliMeta(version='2.6.0', config_stream='3.0.2'),
        ),
    ):
        result = run_command(cleanup_node, ['--yes'])
        assert result.exit_code == 0
        cleanup_mock.assert_called_once_with(
            node_mode=NodeMode.PASSIVE, prune=False, env={'SCHAIN_NAME': 'test'})
