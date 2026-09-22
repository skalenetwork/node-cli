import json
from unittest.mock import Mock

import pytest
import requests_mock

from node_cli.cli.sgx import renew, status
from node_cli.core import sgx as core_sgx
from node_cli.utils.exit_codes import CLIExitCodes
from tests.fixtures.settings import NODE_SKALE_ACTIVE
from tests.fixtures.sgx import FakeSgxWallet
from tests.helper import run_command

SETTINGS_SGX_URL = NODE_SKALE_ACTIVE['sgx_url']


@pytest.fixture
def certs_dir(tmp_path, monkeypatch):
    directory = tmp_path / 'node_data' / 'sgx_certs'
    directory.mkdir(parents=True)
    monkeypatch.setattr(core_sgx, 'SGX_CERTS_PATH', str(directory))
    monkeypatch.setattr(core_sgx, 'SGX_CERTS_BACKUP_PATH', str(directory.parent / 'backup'))
    monkeypatch.setattr(core_sgx, 'SGX_SIGN_POLL_INTERVAL', 0)
    return directory


@pytest.fixture
def rpc():
    with requests_mock.Mocker() as mock:
        yield mock


def test_status_without_certificate(certs_dir):
    result = run_command(status)
    assert result.exit_code == 0
    assert 'Private key' in result.output
    # three file rows plus the notice
    assert result.output.count('missing') == 4
    assert 'skale sgx renew' in result.output


def test_status_shows_certificate_details(certs_dir, rpc):
    FakeSgxWallet(rpc).issue_files(certs_dir)
    result = run_command(status)
    assert result.exit_code == 0
    assert 'sgx-wallet-ca' in result.output
    assert 'yes' in result.output
    assert 'renew' not in result.output


def test_status_json(certs_dir, rpc):
    FakeSgxWallet(rpc).issue_files(certs_dir)
    result = run_command(status, ['--json'])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data['complete'] is True
    assert data['key_matches'] is True
    assert data['issuer'] == 'sgx-wallet-ca'


def test_status_check_uses_configured_sgx_url(certs_dir, rpc, skale_active_settings):
    wallet = FakeSgxWallet(rpc, SETTINGS_SGX_URL)
    wallet.issue_files(certs_dir)
    result = run_command(status, ['--check'])
    assert result.exit_code == 0, result.output
    assert 'accepted the certificate, version 1.83.0' in result.output
    assert wallet.calls == [('sgx', 'getServerVersion')]


def test_status_check_reports_rejection(certs_dir, rpc, skale_active_settings):
    FakeSgxWallet(rpc, SETTINGS_SGX_URL, reject_clients=True).issue_files(certs_dir)
    result = run_command(status, ['--check', '--json'])
    assert result.exit_code == CLIExitCodes.OPERATION_EXECUTION_ERROR.value
    assert 'rejected the TLS connection' in result.output


def test_status_check_needs_an_sgx_node(certs_dir, skale_passive_settings):
    result = run_command(status, ['--check'])
    assert result.exit_code == CLIExitCodes.NODE_STATE_ERROR.value
    assert 'no SGX server configured' in result.output


def test_renew_asks_for_confirmation(certs_dir, monkeypatch):
    core = Mock(side_effect=AssertionError('must not run'))
    monkeypatch.setattr('node_cli.cli.sgx.renew_certificate', core)
    result = run_command(renew, input='n\n')
    assert result.exit_code == 1
    assert 'Aborted' in result.output
    core.assert_not_called()


def test_renew_replaces_certificate(
    certs_dir, rpc, inited_node, skale_active_settings, mocked_g_config
):
    wallet = FakeSgxWallet(rpc, SETTINGS_SGX_URL)
    wallet.issue_files(certs_dir)
    before = {path.name: path.read_bytes() for path in certs_dir.iterdir()}
    result = run_command(renew, ['--yes'])
    assert result.exit_code == 0, result.output
    assert 'hash: ' in result.output
    assert 'accepted the new certificate' in result.output
    assert 'Previous certificate files were copied to' in result.output
    assert 'New SGX client certificate installed' in result.output
    after = {path.name: path.read_bytes() for path in certs_dir.iterdir()}
    assert sorted(after) == ['sgx.crt', 'sgx.csr', 'sgx.key']
    assert after != before
    assert wallet.calls[-1] == ('sgx', 'getServerVersion')


def test_renew_skip_verify_and_timeout_flags(
    certs_dir, rpc, inited_node, skale_active_settings, mocked_g_config
):
    wallet = FakeSgxWallet(rpc, SETTINGS_SGX_URL, reject_clients=True)
    result = run_command(renew, ['--yes', '--skip-verify', '--timeout', '5'])
    assert result.exit_code == 0, result.output
    assert ('sgx', 'getServerVersion') not in wallet.calls
    assert 'Previous certificate files' not in result.output


def test_renew_needs_an_sgx_node(certs_dir, inited_node, skale_passive_settings, mocked_g_config):
    result = run_command(renew, ['--yes'])
    assert result.exit_code == CLIExitCodes.NODE_STATE_ERROR.value
    assert 'no SGX server configured' in result.output


def test_renew_reports_failures(
    certs_dir, inited_node, skale_active_settings, mocked_g_config, monkeypatch
):
    core = Mock(side_effect=core_sgx.SgxCertificateError('SGX server refused signCertificate'))
    monkeypatch.setattr('node_cli.cli.sgx.renew_certificate', core)
    result = run_command(renew, ['--yes'])
    assert result.exit_code == CLIExitCodes.OPERATION_EXECUTION_ERROR.value
    assert 'SGX server refused signCertificate' in result.output
    core.assert_called_once_with(SETTINGS_SGX_URL, timeout=600, verify=True, log=print)
