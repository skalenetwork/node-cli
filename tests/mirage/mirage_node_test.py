from unittest import mock

import freezegun
import pytest

from node_cli.configs import SKALE_DIR
from node_cli.configs.user import SKALE_DIR_ENV_FILEPATH
from node_cli.mirage.mirage_boot import init as init_boot
from node_cli.mirage.mirage_boot import update
from node_cli.mirage.mirage_node import cleanup, migrate_from_boot, request_repair, restore_mirage
from node_cli.operations.mirage import MirageUpdateType
from node_cli.utils.node_type import NodeType
from tests.helper import CURRENT_DATETIME, CURRENT_TIMESTAMP


@mock.patch('node_cli.mirage.mirage_node.time.sleep')
@mock.patch('node_cli.mirage.mirage_node.restore_mirage_op')
@mock.patch('node_cli.mirage.mirage_node.save_env_params')
@mock.patch('node_cli.mirage.mirage_node.compose_node_env')
def test_restore_mirage(
    mock_compose_env,
    mock_save_env,
    mock_restore_op,
    mock_sleep,
    valid_env_file,
    ensure_meta_removed,
):
    mock_env = {'ENV_TYPE': 'devnet'}
    mock_compose_env.return_value = mock_env
    mock_restore_op.return_value = True
    backup_path = '/fake/backup'

    restore_mirage(backup_path, valid_env_file)

    mock_compose_env.assert_called_once_with(valid_env_file, node_type=NodeType.MIRAGE)
    mock_save_env.assert_called_once_with(valid_env_file)
    expected_env = {**mock_env, 'SKALE_DIR': SKALE_DIR}
    mock_restore_op.assert_called_once_with(expected_env, backup_path, config_only=False)
    mock_sleep.assert_called_once()


@mock.patch('node_cli.mirage.mirage_boot.is_base_containers_alive', return_value=True)
@mock.patch('node_cli.mirage.mirage_boot.time.sleep')
@mock.patch('node_cli.mirage.mirage_boot.init_mirage_boot_op')
@mock.patch('node_cli.mirage.mirage_boot.compose_node_env')
def test_init_mirage_boot(
    mock_compose_env,
    mock_init_op,
    mock_sleep,
    mock_is_alive,
    valid_env_file,
    ensure_meta_removed,
):
    mock_env = {'ENV_TYPE': 'devnet'}
    mock_compose_env.return_value = mock_env

    init_boot(valid_env_file)

    mock_compose_env.assert_called_once_with(
        valid_env_file,
        node_type=NodeType.MIRAGE,
        is_mirage_boot=True,
    )
    mock_init_op.assert_called_once_with(valid_env_file, mock_env)
    mock_sleep.assert_called_once()
    mock_is_alive.assert_called_once_with(node_type=NodeType.MIRAGE, is_mirage_boot=True)


@mock.patch('node_cli.utils.decorators.is_user_valid', return_value=True)
@mock.patch('node_cli.mirage.mirage_boot.is_base_containers_alive', return_value=True)
@mock.patch('node_cli.mirage.mirage_boot.time.sleep')
@mock.patch('node_cli.mirage.mirage_boot.update_mirage_boot_op')
@mock.patch('node_cli.mirage.mirage_boot.compose_node_env')
def test_update_mirage_boot(
    mock_compose_env,
    mock_update_op,
    mock_sleep,
    mock_is_alive,
    mock_is_user_valid,
    valid_env_file,
    inited_node,
    resource_alloc,
    meta_file_v3,
):
    mock_env = {'ENV_TYPE': 'devnet'}
    mock_compose_env.return_value = mock_env
    mock_update_op.return_value = True
    pull_config_for_schain = 'mirage'

    update(valid_env_file, pull_config_for_schain)

    mock_compose_env.assert_called_once_with(
        valid_env_file,
        inited_node=True,
        sync_schains=False,
        pull_config_for_schain=pull_config_for_schain,
        node_type=NodeType.MIRAGE,
        is_mirage_boot=True,
    )
    mock_update_op.assert_called_once_with(valid_env_file, mock_env)
    mock_sleep.assert_called_once()
    mock_is_alive.assert_called_once_with(node_type=NodeType.MIRAGE, is_mirage_boot=True)


@mock.patch('node_cli.mirage.mirage_node.update_mirage_op')
@mock.patch('node_cli.mirage.mirage_node.compose_node_env')
@mock.patch('node_cli.utils.decorators.is_user_valid', return_value=True)
def test_migrate_from_boot(
    mock_is_user_valid,
    mock_compose_env,
    mock_migrate_op,
    valid_env_file,
    inited_node,
    resource_alloc,
    meta_file_v3,
):
    mock_env = {'ENV_TYPE': 'devnet'}
    mock_compose_env.return_value = mock_env
    mock_migrate_op.return_value = True

    migrate_from_boot(valid_env_file)

    mock_compose_env.assert_called_once_with(
        valid_env_file,
        inited_node=True,
        sync_schains=False,
        node_type=NodeType.MIRAGE,
    )
    mock_migrate_op.assert_called_once_with(
        valid_env_file, mock_env, update_type=MirageUpdateType.FROM_BOOT
    )


@freezegun.freeze_time(CURRENT_DATETIME)
@mock.patch('node_cli.mirage.mirage_node.compose_node_env', return_value={'ENV_TYPE': 'devnet'})
@mock.patch('node_cli.mirage.record.chain_record.get_mirage_chain_name', return_value='test')
def test_mirage_repair(compose_node_env_mock, get_static_params_mock, redis_client, inited_node):
    request_repair()
    assert redis_client.get('test_repair_ts') == f'{CURRENT_TIMESTAMP}'.encode('utf-8')
    assert redis_client.get('test_snapshot_from') == b''
    request_repair(snapshot_from='127.0.0.1')
    assert redis_client.get('test_repair_ts') == f'{CURRENT_TIMESTAMP}'.encode('utf-8')
    assert redis_client.get('test_snapshot_from') == b'127.0.0.1'


@mock.patch('node_cli.utils.decorators.is_user_valid', return_value=True)
@mock.patch('node_cli.mirage.mirage_node.cleanup_docker_configuration')
@mock.patch('node_cli.mirage.mirage_node.cleanup_mirage_op')
@mock.patch('node_cli.mirage.mirage_node.compose_node_env')
def test_cleanup_success(
    mock_compose_env,
    mock_cleanup_mirage_op,
    mock_cleanup_docker_config,
    mock_is_user_valid,
    inited_node,
    resource_alloc,
    meta_file_v3,
):
    mock_env = {'ENV_TYPE': 'devnet'}
    mock_compose_env.return_value = mock_env

    cleanup()

    mock_compose_env.assert_called_once_with(
        SKALE_DIR_ENV_FILEPATH, save=False, node_type=NodeType.MIRAGE
    )
    mock_cleanup_mirage_op.assert_called_once_with(mock_env)
    mock_cleanup_docker_config.assert_called_once()


@mock.patch('node_cli.utils.decorators.is_user_valid', return_value=True)
@mock.patch('node_cli.mirage.mirage_node.cleanup_docker_configuration')
@mock.patch('node_cli.mirage.mirage_node.cleanup_mirage_op')
@mock.patch('node_cli.mirage.mirage_node.compose_node_env')
def test_cleanup_calls_operations_in_correct_order(
    mock_compose_env,
    mock_cleanup_mirage_op,
    mock_cleanup_docker_config,
    mock_is_user_valid,
    inited_node,
    resource_alloc,
    meta_file_v3,
):
    from node_cli.mirage.mirage_node import cleanup

    mock_env = {'ENV_TYPE': 'devnet'}
    mock_compose_env.return_value = mock_env

    manager = mock.Mock()
    manager.attach_mock(mock_compose_env, 'compose_env')
    manager.attach_mock(mock_cleanup_mirage_op, 'cleanup_mirage_op')
    manager.attach_mock(mock_cleanup_docker_config, 'cleanup_docker_config')

    cleanup()

    expected_calls = [
        mock.call.compose_env(mock.ANY, save=False, node_type=mock.ANY),
        mock.call.cleanup_mirage_op(mock_env),
        mock.call.cleanup_docker_config(),
    ]
    manager.assert_has_calls(expected_calls, any_order=False)


@mock.patch('node_cli.utils.decorators.is_user_valid', return_value=True)
@mock.patch('node_cli.mirage.mirage_node.cleanup_docker_configuration')
@mock.patch(
    'node_cli.mirage.mirage_node.cleanup_mirage_op', side_effect=Exception('Cleanup failed')
)
@mock.patch('node_cli.mirage.mirage_node.compose_node_env')
def test_cleanup_continues_after_mirage_op_error(
    mock_compose_env,
    mock_cleanup_mirage_op,
    mock_cleanup_docker_config,
    mock_is_user_valid,
    inited_node,
    resource_alloc,
    meta_file_v3,
):
    mock_env = {'ENV_TYPE': 'devnet'}
    mock_compose_env.return_value = mock_env

    with pytest.raises(Exception, match='Cleanup failed'):
        cleanup()

    mock_compose_env.assert_called_once()
    mock_cleanup_mirage_op.assert_called_once_with(mock_env)
    mock_cleanup_docker_config.assert_not_called()


@mock.patch('node_cli.utils.decorators.is_user_valid', return_value=False)
def test_cleanup_fails_when_user_invalid(
    mock_is_user_valid,
    inited_node,
    resource_alloc,
    meta_file_v3,
):
    """Test that cleanup fails when user validation fails"""
    import pytest

    from node_cli.mirage.mirage_node import cleanup

    with pytest.raises(SystemExit):
        cleanup()


def test_cleanup_fails_when_not_inited(ensure_meta_removed):
    import pytest

    with pytest.raises(SystemExit):
        cleanup()


@mock.patch('node_cli.utils.decorators.is_user_valid', return_value=True)
@mock.patch('node_cli.mirage.mirage_node.cleanup_docker_configuration')
@mock.patch('node_cli.mirage.mirage_node.cleanup_mirage_op')
@mock.patch('node_cli.mirage.mirage_node.compose_node_env')
@mock.patch('node_cli.mirage.mirage_node.logger')
def test_cleanup_logs_success_message(
    mock_logger,
    mock_compose_env,
    mock_cleanup_mirage_op,
    mock_cleanup_docker_config,
    mock_is_user_valid,
    inited_node,
    resource_alloc,
    meta_file_v3,
):
    mock_env = {'ENV_TYPE': 'devnet'}
    mock_compose_env.return_value = mock_env

    cleanup()

    mock_logger.info.assert_called_once_with(
        'Mirage node was cleaned up, all containers and data removed'
    )
