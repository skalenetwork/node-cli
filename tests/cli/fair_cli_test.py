import pathlib
from unittest import mock

from click.testing import CliRunner
from node_cli.cli.fair_boot import (
    init_boot,
    register_boot,
    signature_boot,
)
from node_cli.cli.fair_node import (
    backup_node,
    cleanup_node,
    migrate_node,
    exit_node,
    restore_node,
)
from node_cli.configs import SKALE_DIR
from node_cli.utils.node_type import NodeMode
from node_cli.utils.meta import CliMeta
from tests.helper import run_command, subprocess_run_mock
from tests.resources_test import BIG_DISK_SIZE

@mock.patch('node_cli.cli.fair_node.restore_fair')
def test_fair_node_restore(mock_restore_core, valid_env_file, tmp_path):
    runner = CliRunner()
    backup_file = tmp_path / 'backup.tar.gz'
    backup_file.touch()
    backup_path = str(backup_file)

    result = runner.invoke(restore_node, [backup_path, valid_env_file])

    assert result.exit_code == 0, f'Output: {result.output}\nException: {result.exception}'
    mock_restore_core.assert_called_once_with(backup_path, valid_env_file, False)


@mock.patch('node_cli.cli.fair_node.restore_fair')
def test_fair_node_restore_config_only(mock_restore_core, valid_env_file, tmp_path):
    runner = CliRunner()
    backup_file = tmp_path / 'backup_config.tar.gz'
    backup_file.touch()
    backup_path = str(backup_file)

    result = runner.invoke(restore_node, [backup_path, valid_env_file, '--config-only'])

    assert result.exit_code == 0, f'Output: {result.output}\nException: {result.exception}'
    mock_restore_core.assert_called_once_with(backup_path, valid_env_file, True)


@mock.patch('node_cli.cli.fair_node.backup')
def test_fair_node_backup(mock_backup_core, tmp_path):
    runner = CliRunner()
    backup_folder = str(tmp_path / 'backups')
    pathlib.Path(backup_folder).mkdir(exist_ok=True)

    result = runner.invoke(backup_node, [backup_folder])

    assert result.exit_code == 0, f'Output: {result.output}\nException: {result.exception}'
    mock_backup_core.assert_called_once_with(backup_folder)


@mock.patch('node_cli.cli.fair_boot.register')
def test_fair_boot_register(mock_register_core):
    runner = CliRunner()
    name = 'test-boot-node'
    ip = '1.2.3.4'
    port = 10001
    domain = 'boot.skale.test'

    result = runner.invoke(
        register_boot, ['--name', name, '--ip', ip, '--port', str(port), '--domain', domain]
    )

    assert result.exit_code == 0, f'Output: {result.output}\nException: {result.exception}'
    mock_register_core.assert_called_once_with(
        name=name, p2p_ip=ip, public_ip=ip, port=port, domain_name=domain
    )


@mock.patch('node_cli.cli.fair_boot.get_node_signature')
def test_fair_boot_signature(mock_signature_core):
    runner = CliRunner()
    validator_id = '101'
    signature_val = '0xdef456'
    mock_signature_core.return_value = signature_val

    result = runner.invoke(signature_boot, [validator_id])

    assert result.exit_code == 0, f'Output: {result.output}\nException: {result.exception}'
    mock_signature_core.assert_called_once_with(validator_id)
    assert f'Signature: {signature_val}' in result.output


@mock.patch('node_cli.cli.fair_boot.init')
def test_fair_boot_init(mock_init_core, valid_env_file):
    runner = CliRunner()
    result = runner.invoke(init_boot, [valid_env_file])

    assert result.exit_code == 0, f'Output: {result.output}\nException: {result.exception}'
    mock_init_core.assert_called_once_with(valid_env_file)


@mock.patch('node_cli.cli.fair_node.migrate_from_boot')
def test_fair_node_migrate(mock_migrate_core, valid_env_file):
    runner = CliRunner()
    result = runner.invoke(migrate_node, ['--yes', valid_env_file])

    assert result.exit_code == 0, f'Output: {result.output}\nException: {result.exception}'
    mock_migrate_core.assert_called_once_with(env_filepath=valid_env_file)


@mock.patch('node_cli.cli.fair_node.exit_fair')
def test_fair_node_exit(mock_exit_core):
    runner = CliRunner()
    result = runner.invoke(exit_node, ['--yes'])

    assert result.exit_code == 0, f'Output: {result.output}\nException: {result.exception}'
    mock_exit_core.assert_called_once()


def test_cleanup_node(mocked_g_config, inited_node):
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
            node_mode=NodeMode.ACTIVE, prune=False, env={'SCHAIN_NAME': 'test'})
