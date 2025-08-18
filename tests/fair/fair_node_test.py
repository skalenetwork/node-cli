from unittest import mock

import pytest

from node_cli.configs import SKALE_DIR
from node_cli.configs.user import SKALE_DIR_ENV_FILEPATH
from node_cli.fair.boot import init as init_boot
from node_cli.fair.boot import update
from node_cli.fair.common import cleanup
from node_cli.fair.active import migrate_from_boot, restore
from node_cli.operations.fair import FairUpdateType
from node_cli.utils.node_type import NodeMode, NodeType


@mock.patch('node_cli.fair.active.time.sleep')
@mock.patch('node_cli.fair.active.restore_fair_op')
@mock.patch('node_cli.fair.active.save_env_params')
@mock.patch('node_cli.fair.active.compose_node_env')
def test_restore_fair(
    mock_compose_env,
    mock_save_env,
    mock_restore_op,
    mock_sleep,
    valid_env_file,
    ensure_meta_removed,
    active_node_option,
):
    mock_env = {'ENV_TYPE': 'devnet'}
    mock_compose_env.return_value = mock_env
    mock_restore_op.return_value = True
    backup_path = '/fake/backup'

    restore(backup_path, valid_env_file)

    mock_compose_env.assert_called_once_with(
        valid_env_file, node_type=NodeType.FAIR, node_mode=NodeMode.ACTIVE
    )
    mock_save_env.assert_called_once_with(valid_env_file)
    expected_env = {**mock_env, 'SKALE_DIR': SKALE_DIR}
    mock_restore_op.assert_called_once_with(
        node_mode=NodeMode.ACTIVE,
        env=expected_env,
        backup_path=backup_path,
        config_only=False,
    )
    mock_sleep.assert_called_once()


@mock.patch('node_cli.fair.boot.is_base_containers_alive', return_value=True)
@mock.patch('node_cli.fair.boot.time.sleep')
@mock.patch('node_cli.fair.boot.init_fair_boot_op')
@mock.patch('node_cli.fair.boot.compose_node_env')
def test_init_fair_boot(
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
        node_type=NodeType.FAIR,
        node_mode=NodeMode.ACTIVE,
        is_fair_boot=True,
    )
    mock_init_op.assert_called_once_with(valid_env_file, mock_env)
    mock_sleep.assert_called_once()
    mock_is_alive.assert_called_once_with(node_type=NodeType.FAIR, is_fair_boot=True)


@mock.patch('node_cli.utils.decorators.is_user_valid', return_value=True)
@mock.patch('node_cli.fair.boot.is_base_containers_alive', return_value=True)
@mock.patch('node_cli.fair.boot.time.sleep')
@mock.patch('node_cli.fair.boot.update_fair_boot_op')
@mock.patch('node_cli.fair.boot.compose_node_env')
def test_update_fair_boot(
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
    pull_config_for_schain = 'fair'

    update(valid_env_file, pull_config_for_schain)

    mock_compose_env.assert_called_once_with(
        valid_env_file,
        inited_node=True,
        sync_schains=False,
        pull_config_for_schain=pull_config_for_schain,
        node_type=NodeType.FAIR,
        node_mode=NodeMode.ACTIVE,
        is_fair_boot=True,
    )
    mock_update_op.assert_called_once_with(valid_env_file, mock_env)
    mock_sleep.assert_called_once()
    mock_is_alive.assert_called_once_with(node_type=NodeType.FAIR, is_fair_boot=True)


@mock.patch('node_cli.fair.active.update_fair_op')
@mock.patch('node_cli.fair.active.compose_node_env')
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
        node_type=NodeType.FAIR,
        node_mode=NodeMode.ACTIVE,
    )
    mock_migrate_op.assert_called_once_with(
        valid_env_file, mock_env, update_type=FairUpdateType.FROM_BOOT, force_skaled_start=False
    )


@mock.patch('node_cli.utils.decorators.is_user_valid', return_value=True)
@mock.patch('node_cli.fair.common.cleanup_docker_configuration')
@mock.patch('node_cli.fair.common.cleanup_fair_op')
@mock.patch('node_cli.fair.common.compose_node_env')
def test_cleanup_success(
    mock_compose_env,
    mock_cleanup_fair_op,
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
        SKALE_DIR_ENV_FILEPATH,
        save=False,
        node_type=NodeType.FAIR,
        node_mode=NodeMode.ACTIVE,
    )
    mock_cleanup_fair_op.assert_called_once_with(node_mode=NodeMode.ACTIVE, env=mock_env)
    mock_cleanup_docker_config.assert_called_once()


@mock.patch('node_cli.utils.decorators.is_user_valid', return_value=True)
@mock.patch('node_cli.fair.common.cleanup_docker_configuration')
@mock.patch('node_cli.fair.common.cleanup_fair_op')
@mock.patch('node_cli.fair.common.compose_node_env')
def test_cleanup_calls_operations_in_correct_order(
    mock_compose_env,
    mock_cleanup_fair_op,
    mock_cleanup_docker_config,
    mock_is_user_valid,
    inited_node,
    resource_alloc,
    meta_file_v3,
    active_node_option,
):
    from node_cli.fair.common import cleanup

    mock_env = {'ENV_TYPE': 'devnet'}
    mock_compose_env.return_value = mock_env

    manager = mock.Mock()
    manager.attach_mock(mock_compose_env, 'compose_env')
    manager.attach_mock(mock_cleanup_fair_op, 'cleanup_fair_op')
    manager.attach_mock(mock_cleanup_docker_config, 'cleanup_docker_config')

    cleanup()

    expected_calls = [
        mock.call.compose_env(mock.ANY, save=False, node_type=mock.ANY, node_mode=NodeMode.ACTIVE),
        mock.call.cleanup_fair_op(node_mode=NodeMode.ACTIVE, env=mock_env),
        mock.call.cleanup_docker_config(),
    ]
    manager.assert_has_calls(expected_calls, any_order=False)


@mock.patch('node_cli.utils.decorators.is_user_valid', return_value=True)
@mock.patch('node_cli.fair.common.cleanup_docker_configuration')
@mock.patch('node_cli.fair.common.cleanup_fair_op', side_effect=Exception('Cleanup failed'))
@mock.patch('node_cli.fair.common.compose_node_env')
def test_cleanup_continues_after_fair_op_error(
    mock_compose_env,
    mock_cleanup_fair_op,
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
    mock_cleanup_fair_op.assert_called_once_with(node_mode=NodeMode.ACTIVE, env=mock_env)
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

    from node_cli.fair.common import cleanup

    with pytest.raises(SystemExit):
        cleanup()


def test_cleanup_fails_when_not_inited(ensure_meta_removed, active_node_option):
    import pytest

    with pytest.raises(SystemExit):
        cleanup()


@mock.patch('node_cli.utils.decorators.is_user_valid', return_value=True)
@mock.patch('node_cli.fair.common.cleanup_docker_configuration')
@mock.patch('node_cli.fair.common.cleanup_fair_op')
@mock.patch('node_cli.fair.common.compose_node_env')
@mock.patch('node_cli.fair.common.logger')
def test_cleanup_logs_success_message(
    mock_logger,
    mock_compose_env,
    mock_cleanup_fair_op,
    mock_cleanup_docker_config,
    mock_is_user_valid,
    inited_node,
    resource_alloc,
    meta_file_v3,
    active_node_option,
):
    mock_env = {'ENV_TYPE': 'devnet'}
    mock_compose_env.return_value = mock_env

    cleanup()

    mock_logger.info.assert_called_once_with(
        'Fair node was cleaned up, all containers and data removed'
    )


@mock.patch('node_cli.utils.decorators.is_user_valid', return_value=True)
@mock.patch('node_cli.fair.active.post_request')
@mock.patch('node_cli.fair.active.is_node_inited', return_value=True)
def test_exit_success(
    mock_is_inited,
    mock_post_request,
    mock_is_user_valid,
    inited_node,
    resource_alloc,
    meta_file_v3,
):
    from node_cli.fair.active import exit

    mock_post_request.return_value = ('ok', {})

    exit()

    mock_post_request.assert_called_once_with(blueprint='fair-node', method='exit', json={})


@mock.patch('node_cli.utils.decorators.is_user_valid', return_value=True)
@mock.patch('node_cli.fair.active.error_exit')
@mock.patch('node_cli.fair.active.post_request')
@mock.patch('node_cli.fair.active.is_node_inited', return_value=True)
def test_exit_error(
    mock_is_inited,
    mock_post_request,
    mock_error_exit,
    mock_is_user_valid,
    inited_node,
    resource_alloc,
    meta_file_v3,
):
    from node_cli.fair.active import exit

    error_msg = 'Exit failed'
    mock_post_request.return_value = ('error', error_msg)

    exit()

    mock_post_request.assert_called_once_with(blueprint='fair-node', method='exit', json={})
    mock_error_exit.assert_called_once_with(error_msg, exit_code=mock.ANY)


@mock.patch('node_cli.utils.decorators.is_user_valid', return_value=True)
@mock.patch('node_cli.fair.active.is_node_inited', return_value=False)
def test_exit_not_inited(
    mock_is_inited,
    mock_is_user_valid,
    inited_node,
    resource_alloc,
    meta_file_v3,
    capsys,
):
    from node_cli.fair.active import exit

    exit()

    captured = capsys.readouterr()
    assert 'Node should be initialized to proceed with operation' in captured.out
