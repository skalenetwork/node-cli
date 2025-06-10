from click.testing import CliRunner
from unittest import mock
import pathlib

from node_cli.cli.mirage_node import (
    restore_node,
    backup_node,
    signature_node,
    init_node as init_node_placeholder,
    register_node as register_node_placeholder,
    update_node as update_node_placeholder,
    migrate_node,
)
from node_cli.cli.mirage_boot import (
    init_boot,
    register_boot,
    signature_boot,
    migrate_boot,
)


@mock.patch('node_cli.cli.mirage_node.restore_mirage')
def test_mirage_node_restore(mock_restore_core, valid_env_file, tmp_path):
    runner = CliRunner()
    backup_file = tmp_path / 'backup.tar.gz'
    backup_file.touch()
    backup_path = str(backup_file)

    result = runner.invoke(restore_node, [backup_path, valid_env_file])

    assert result.exit_code == 0, f'Output: {result.output}\nException: {result.exception}'
    mock_restore_core.assert_called_once_with(backup_path, valid_env_file, False)


@mock.patch('node_cli.cli.mirage_node.restore_mirage')
def test_mirage_node_restore_config_only(mock_restore_core, valid_env_file, tmp_path):
    runner = CliRunner()
    backup_file = tmp_path / 'backup_config.tar.gz'
    backup_file.touch()
    backup_path = str(backup_file)

    result = runner.invoke(restore_node, [backup_path, valid_env_file, '--config-only'])

    assert result.exit_code == 0, f'Output: {result.output}\nException: {result.exception}'
    mock_restore_core.assert_called_once_with(backup_path, valid_env_file, True)


@mock.patch('node_cli.cli.mirage_node.backup')
def test_mirage_node_backup(mock_backup_core, tmp_path):
    runner = CliRunner()
    backup_folder = str(tmp_path / 'backups')
    pathlib.Path(backup_folder).mkdir(exist_ok=True)

    result = runner.invoke(backup_node, [backup_folder])

    assert result.exit_code == 0, f'Output: {result.output}\nException: {result.exception}'
    mock_backup_core.assert_called_once_with(backup_folder)


@mock.patch('node_cli.cli.mirage_node.get_node_signature')
def test_mirage_node_signature(mock_signature_core):
    runner = CliRunner()
    validator_id = '42'
    signature_val = '0xabc123'
    mock_signature_core.return_value = signature_val

    result = runner.invoke(signature_node, [validator_id])

    assert result.exit_code == 0, f'Output: {result.output}\nException: {result.exception}'
    mock_signature_core.assert_called_once_with(validator_id)
    assert f'Signature: {signature_val}' in result.output


@mock.patch('node_cli.cli.mirage_node.get_node_signature')
def test_mirage_node_signature_error(mock_signature_core):
    runner = CliRunner()
    validator_id = '43'
    error_msg = 'Core layer error'
    mock_signature_core.return_value = {'error': True, 'message': error_msg}

    result = runner.invoke(signature_node, [validator_id])

    assert result.exit_code != 0, f'Output: {result.output}\nException: {result.exception}'
    mock_signature_core.assert_called_once_with(validator_id)
    assert error_msg in result.output


def test_mirage_node_init_placeholder():
    runner = CliRunner()
    result = runner.invoke(init_node_placeholder, [])

    assert result.exit_code == 0, f'Output: {result.output}\nException: {result.exception}'
    assert "Placeholder: Command 'mirage node init' is not yet implemented." in result.output


def test_mirage_node_register_placeholder():
    runner = CliRunner()
    result = runner.invoke(register_node_placeholder, [])

    assert result.exit_code == 0, f'Output: {result.output}\nException: {result.exception}'
    assert "Placeholder: Command 'mirage node register' is not yet implemented." in result.output


def test_mirage_node_update_placeholder(valid_env_file):
    runner = CliRunner()
    result = runner.invoke(update_node_placeholder, ['--yes', valid_env_file])

    assert result.exit_code == 0, f'Output: {result.output}\nException: {result.exception}'
    assert "Placeholder: Command 'mirage node update' is not yet implemented." in result.output


@mock.patch('node_cli.cli.mirage_boot.register')
def test_mirage_boot_register(mock_register_core):
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


@mock.patch('node_cli.cli.mirage_boot.get_node_signature')
def test_mirage_boot_signature(mock_signature_core):
    runner = CliRunner()
    validator_id = '101'
    signature_val = '0xdef456'
    mock_signature_core.return_value = signature_val

    result = runner.invoke(signature_boot, [validator_id])

    assert result.exit_code == 0, f'Output: {result.output}\nException: {result.exception}'
    mock_signature_core.assert_called_once_with(validator_id)
    assert f'Signature: {signature_val}' in result.output


@mock.patch('node_cli.cli.mirage_boot.init')
def test_mirage_boot_init(mock_init_core, valid_env_file):
    runner = CliRunner()
    result = runner.invoke(init_boot, [valid_env_file])

    assert result.exit_code == 0, f'Output: {result.output}\nException: {result.exception}'
    mock_init_core.assert_called_once_with(valid_env_file)


@mock.patch('node_cli.cli.mirage_boot.migrate')
def test_mirage_boot_migrate(mock_migrate_core, valid_env_file):
    runner = CliRunner()
    result = runner.invoke(migrate_boot, ['--yes', valid_env_file])

    assert result.exit_code == 0, f'Output: {result.output}\nException: {result.exception}'
    mock_migrate_core.assert_called_once_with(valid_env_file, None)


@mock.patch('node_cli.cli.mirage_boot.migrate')
def test_mirage_boot_migrate_pull_config(mock_migrate_core, valid_env_file):
    runner = CliRunner()
    schain_name = 'my-schain-config'
    result = runner.invoke(migrate_boot, ['--yes', '--pull-config', schain_name, valid_env_file])

    assert result.exit_code == 0, f'Output: {result.output}\nException: {result.exception}'
    mock_migrate_core.assert_called_once_with(valid_env_file, schain_name)


@mock.patch('node_cli.cli.mirage_node.migrate_from_boot')
def test_mirage_node_migrate(mock_migrate_core, valid_env_file):
    runner = CliRunner()
    result = runner.invoke(migrate_node, ['--yes', valid_env_file])

    assert result.exit_code == 0, f'Output: {result.output}\nException: {result.exception}'
    mock_migrate_core.assert_called_once_with(valid_env_file, None)
