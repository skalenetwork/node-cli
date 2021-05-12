import os
import pathlib

import pytest

from core.ssl import check_cert, SSLServerError, upload_certs
from tools.helper import run_cmd


@pytest.fixture
def cert_key_pair():
    cert_path = os.path.abspath('ssl-test-cert')
    key_path = os.path.abspath('ssl-test-key')
    run_cmd([
        'openssl', 'req',
        '-newkey', 'rsa:4096',
        '-x509',
        '-sha256',
        '-days', '365',
        '-nodes',
        '-subj', '/',
        '-out', cert_path,
        '-keyout', key_path
    ])
    yield cert_path, key_path
    pathlib.Path(cert_path).unlink(missing_ok=True)
    pathlib.Path(key_path).unlink(missing_ok=True)


@pytest.fixture
def bad_cert(cert_key_pair):
    cert, key = cert_key_pair
    with open(cert, 'w') as cert_file:
        cert_file.write('WRONG CERT')
    yield cert, key


@pytest.fixture
def bad_key(cert_key_pair):
    cert, key = cert_key_pair
    with open(key, 'w') as key_file:
        key_file.write('WRONG KEY')
    yield cert, key


def test_verify_cert(cert_key_pair):
    cert, key = cert_key_pair
    check_cert(cert, key, no_client=True)


def test_verify_cert_bad_cert(bad_cert):
    cert, key = bad_cert
    with pytest.raises(SSLServerError):
        check_cert(cert, key, no_client=True)


def test_verify_cert_bad_key(bad_key):
    cert, key = bad_key
    with pytest.raises(SSLServerError):
        check_cert(cert, key, no_client=True)


@pytest.mark.skip
def test_upload_certs(cert_key_pair):
    cert, key = cert_key_pair
    result = upload_certs(cert, key, force=False)
    assert result is None
    result = upload_certs(cert, key, force=True)
    assert result is None
