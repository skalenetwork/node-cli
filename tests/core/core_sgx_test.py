import json
import stat
from pathlib import Path

import pytest
import requests_mock

from node_cli.core import sgx
from tests.fixtures.sgx import SGX_URL, FakeSgxWallet

CERT_FILES = ['sgx.crt', 'sgx.csr', 'sgx.key']


@pytest.fixture(autouse=True)
def fast_polling(monkeypatch):
    monkeypatch.setattr(sgx, 'SGX_SIGN_POLL_INTERVAL', 0)


@pytest.fixture
def rpc():
    with requests_mock.Mocker() as mock:
        yield mock


@pytest.fixture
def certs_dir(tmp_path):
    directory = tmp_path / 'node_data' / 'sgx_certs'
    directory.mkdir(parents=True)
    return directory


def snapshot(directory: Path) -> dict[str, bytes]:
    return {path.name: path.read_bytes() for path in directory.iterdir()}


def names(directory: Path) -> list[str]:
    return sorted(path.name for path in directory.iterdir())


@pytest.mark.parametrize(
    'sgx_url, expected',
    [
        ('https://sgx.example.com:1026', 'http://sgx.example.com:1027'),
        ('http://127.0.0.1:2026/', 'http://127.0.0.1:2027'),
        ('https://[fd00::1]:1026', 'http://[fd00::1]:1027'),
    ],
)
def test_csr_server_url(sgx_url, expected):
    assert sgx.csr_server_url(sgx_url) == expected


@pytest.mark.parametrize('sgx_url', ['https://sgx.example.com', 'ftp://host:1026', 'nonsense'])
def test_csr_server_url_rejects_incomplete_urls(sgx_url):
    with pytest.raises(sgx.SgxCertificateError):
        sgx.csr_server_url(sgx_url)


def test_status_reports_missing_files(certs_dir):
    status = sgx.get_certificate_status(certs_dir)
    assert status['complete'] is False
    assert status['present'] == {'key': False, 'csr': False, 'crt': False}
    assert 'subject' not in status
    assert sgx.get_certificate_status(certs_dir / 'absent')['complete'] is False


def test_status_describes_certificate(certs_dir, rpc):
    wallet = FakeSgxWallet(rpc)
    wallet.issue_files(certs_dir)
    status = sgx.get_certificate_status(certs_dir)
    assert status['complete'] is True
    assert status['subject'] == 'ab' * 32
    assert status['issuer'] == 'sgx-wallet-ca'
    assert status['key_matches'] is True
    assert status['expired'] is False
    assert status['not_yet_valid'] is False
    assert status['expires_soon'] is False
    assert 363 <= status['days_left'] <= 365
    assert status['fingerprint_sha256'] == wallet.last_issued.fingerprint(sgx.hashes.SHA256()).hex(
        ':'
    )
    json.dumps(status)


def test_status_detects_key_mismatch_and_partial_sets(certs_dir, rpc):
    wallet = FakeSgxWallet(rpc)
    wallet.issue_files(certs_dir)
    other = certs_dir.parent / 'other'
    wallet.issue_files(other)
    (certs_dir / 'sgx.key').write_bytes((other / 'sgx.key').read_bytes())
    assert sgx.get_certificate_status(certs_dir)['key_matches'] is False
    (certs_dir / 'sgx.key').write_text('not a key')
    assert sgx.get_certificate_status(certs_dir)['key_matches'] is False
    (certs_dir / 'sgx.key').unlink()
    status = sgx.get_certificate_status(certs_dir)
    assert status['key_matches'] is None
    assert status['complete'] is False


def test_status_rejects_unreadable_certificate(certs_dir):
    (certs_dir / 'sgx.crt').write_text('garbage')
    with pytest.raises(sgx.SgxCertificateError, match='Cannot read certificate'):
        sgx.get_certificate_status(certs_dir)


def test_check_certificate(certs_dir, rpc):
    wallet = FakeSgxWallet(rpc)
    with pytest.raises(sgx.SgxCertificateError, match='missing files: key, crt'):
        sgx.check_certificate(SGX_URL, certs_dir)
    wallet.issue_files(certs_dir)
    assert sgx.check_certificate(SGX_URL, certs_dir) == '1.83.0'
    assert wallet.client_certs == [(str(certs_dir / 'sgx.crt'), str(certs_dir / 'sgx.key'))]


def test_check_certificate_reports_rejection(certs_dir, rpc):
    FakeSgxWallet(rpc, reject_clients=True).issue_files(certs_dir)
    with pytest.raises(sgx.SgxCertificateError, match='rejected the TLS connection'):
        sgx.check_certificate(SGX_URL, certs_dir)


def test_renew_installs_new_certificate_and_keeps_backup(certs_dir, rpc):
    wallet = FakeSgxWallet(rpc)
    wallet.issue_files(certs_dir)
    before = snapshot(certs_dir)
    backups = certs_dir.parent / 'sgx_certs_backup'
    messages: list[str] = []

    result = sgx.renew_certificate(
        SGX_URL, directory=certs_dir, backup_root=backups, log=messages.append
    )

    assert names(certs_dir) == CERT_FILES
    assert names(certs_dir.parent) == ['sgx_certs', 'sgx_certs_backup']
    after = snapshot(certs_dir)
    assert all(after[name] != before[name] for name in CERT_FILES)
    assert stat.S_IMODE((certs_dir / 'sgx.key').stat().st_mode) == 0o600
    assert stat.S_IMODE((certs_dir / 'sgx.crt').stat().st_mode) == 0o644
    assert stat.S_IMODE((certs_dir / 'sgx.csr').stat().st_mode) == 0o644

    status = sgx.get_certificate_status(certs_dir)
    assert status['complete'] and status['key_matches'] and status['issuer'] == 'sgx-wallet-ca'
    assert status['fingerprint_sha256'] == wallet.last_issued.fingerprint(sgx.hashes.SHA256()).hex(
        ':'
    )
    assert result['server_version'] == '1.83.0'
    assert result['fingerprint_sha256'] == status['fingerprint_sha256']

    backup = Path(result['backup'])
    assert backup.parent == backups
    assert stat.S_IMODE(backups.stat().st_mode) == 0o700
    assert snapshot(backup) == before

    assert wallet.calls == [
        ('csr', 'signCertificate'),
        ('csr', 'getCertificate'),
        ('sgx', 'getServerVersion'),
    ]
    staged_crt, staged_key = wallet.client_certs[0]
    assert Path(staged_crt).parent != certs_dir
    assert Path(staged_crt).parent.name.startswith('.sgx_certs.')
    assert not Path(staged_crt).exists() and not Path(staged_key).exists()
    assert any('hash: ' in message for message in messages)
    assert not any('Waiting' in message for message in messages)


def test_renew_waits_for_manual_approval(certs_dir, rpc):
    wallet = FakeSgxWallet(rpc, pending_polls=2)
    messages: list[str] = []
    sgx.renew_certificate(SGX_URL, directory=certs_dir, log=messages.append, timeout=30)
    assert wallet.calls.count(('csr', 'getCertificate')) == 3
    assert sum('Waiting' in message for message in messages) == 1
    assert sgx.get_certificate_status(certs_dir)['complete']


def test_renew_times_out_without_touching_current_files(certs_dir, rpc):
    wallet = FakeSgxWallet(rpc, pending_polls=10**6)
    wallet.issue_files(certs_dir)
    before = snapshot(certs_dir)
    backups = certs_dir.parent / 'sgx_certs_backup'
    with pytest.raises(sgx.SgxCertificateError, match='did not sign the request within 0'):
        sgx.renew_certificate(SGX_URL, directory=certs_dir, backup_root=backups, timeout=0)
    assert snapshot(certs_dir) == before
    assert names(certs_dir.parent) == ['sgx_certs']
    assert ('sgx', 'getServerVersion') not in wallet.calls


def test_renew_aborts_when_server_rejects_new_certificate(certs_dir, rpc):
    wallet = FakeSgxWallet(rpc, reject_clients=True)
    wallet.issue_files(certs_dir)
    before = snapshot(certs_dir)
    with pytest.raises(sgx.SgxCertificateError, match='rejected the TLS connection'):
        sgx.renew_certificate(SGX_URL, directory=certs_dir)
    assert snapshot(certs_dir) == before
    assert names(certs_dir.parent) == ['sgx_certs']


def test_renew_can_skip_server_verification(certs_dir, rpc):
    wallet = FakeSgxWallet(rpc, reject_clients=True)
    result = sgx.renew_certificate(SGX_URL, directory=certs_dir, verify=False)
    assert result['server_version'] is None
    assert result['backup'] is None
    assert ('sgx', 'getServerVersion') not in wallet.calls
    assert names(certs_dir) == CERT_FILES
    assert names(certs_dir.parent) == ['sgx_certs']


def test_renew_rejects_certificate_issued_for_another_key(certs_dir, rpc):
    wallet = FakeSgxWallet(rpc, wrong_key=True)
    wallet.issue_files(certs_dir)
    before = snapshot(certs_dir)
    with pytest.raises(sgx.SgxCertificateError, match='does not match the generated key'):
        sgx.renew_certificate(SGX_URL, directory=certs_dir)
    assert snapshot(certs_dir) == before


def test_renew_reports_signing_refusal(certs_dir, rpc):
    wallet = FakeSgxWallet(rpc, sign_error='CSR rejected by policy')
    wallet.issue_files(certs_dir)
    before = snapshot(certs_dir)
    with pytest.raises(sgx.SgxCertificateError, match='CSR rejected by policy'):
        sgx.renew_certificate(SGX_URL, directory=certs_dir)
    assert snapshot(certs_dir) == before
    assert wallet.calls == [('csr', 'signCertificate')]


def test_renew_reports_transport_errors(certs_dir, rpc):
    rpc.post('http://127.0.0.1:1027/', status_code=502)
    with pytest.raises(sgx.SgxCertificateError, match='Cannot call signCertificate'):
        sgx.renew_certificate(SGX_URL, directory=certs_dir)
    assert names(certs_dir) == []
    assert names(certs_dir.parent) == ['sgx_certs']


def test_renew_creates_missing_directory(tmp_path, rpc):
    FakeSgxWallet(rpc)
    directory = tmp_path / 'node_data' / 'sgx_certs'
    result = sgx.renew_certificate(SGX_URL, directory=directory)
    assert result['backup'] is None
    assert names(directory) == CERT_FILES


def test_renew_reports_unwritable_directory(tmp_path, rpc):
    FakeSgxWallet(rpc)
    parent = tmp_path / 'node_data'
    parent.mkdir(mode=0o500)
    try:
        with pytest.raises(sgx.SgxCertificateError, match='Cannot prepare certificate files'):
            sgx.renew_certificate(SGX_URL, directory=parent / 'sgx_certs')
    finally:
        parent.chmod(0o700)
