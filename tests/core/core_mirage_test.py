from unittest import mock

from node_cli.configs import SKALE_DIR
from node_cli.core.mirage_boot import init as init_boot, migrate, update
from node_cli.core.mirage_node import restore_mirage, migrate_from_boot
from node_cli.operations.mirage import MirageUpdateType
from node_cli.utils.node_type import NodeType


@mock.patch('node_cli.core.mirage_node.time.sleep')
@mock.patch('node_cli.core.mirage_node.restore_mirage_op')
@mock.patch('node_cli.core.mirage_node.save_env_params')
@mock.patch('node_cli.core.mirage_node.compose_node_env')
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


@mock.patch('node_cli.core.mirage_boot.is_base_containers_alive', return_value=True)
@mock.patch('node_cli.core.mirage_boot.time.sleep')
@mock.patch('node_cli.core.mirage_boot.init_mirage_boot_op')
@mock.patch('node_cli.core.mirage_boot.compose_node_env')
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
@mock.patch('node_cli.core.mirage_boot.is_base_containers_alive', return_value=True)
@mock.patch('node_cli.core.mirage_boot.time.sleep')
@mock.patch('node_cli.core.mirage_boot.migrate_mirage_boot_op')
@mock.patch('node_cli.core.mirage_boot.compose_node_env')
def test_migrate_mirage_boot(
    mock_compose_env,
    mock_migrate_op,
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
    mock_migrate_op.return_value = True
    pull_config_for_schain = 'mirage'

    migrate(valid_env_file, pull_config_for_schain)

    mock_compose_env.assert_called_once_with(
        valid_env_file,
        inited_node=True,
        sync_schains=False,
        pull_config_for_schain=pull_config_for_schain,
        node_type=NodeType.MIRAGE,
    )
    mock_migrate_op.assert_called_once_with(valid_env_file, mock_env)
    mock_sleep.assert_called_once()
    mock_is_alive.assert_called_once_with(node_type=NodeType.MIRAGE)


@mock.patch('node_cli.utils.decorators.is_user_valid', return_value=True)
@mock.patch('node_cli.core.mirage_boot.is_base_containers_alive', return_value=True)
@mock.patch('node_cli.core.mirage_boot.time.sleep')
@mock.patch('node_cli.core.mirage_boot.update_mirage_boot_op')
@mock.patch('node_cli.core.mirage_boot.compose_node_env')
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


@mock.patch('node_cli.core.mirage_node.update_mirage_op')
@mock.patch('node_cli.core.mirage_node.compose_node_env')
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
        valid_env_file, mock_env, update_type=MirageUpdateType.INFRA_ONLY
    )
