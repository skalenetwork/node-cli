import os
import pathlib

import mock
import pytest

from core.ssl import check_cert_openssl, SSLHealthcheckError, upload_cert
from tools.helper import run_cmd


HOST = '127.0.0.1'


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
    if os.path.isfile(cert_path):
        pathlib.Path(cert_path).unlink()
    if os.path.isfile(key_path):
        pathlib.Path(key_path).unlink()


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
    check_cert_openssl(cert, key, host=HOST, no_client=True)


def test_verify_cert_self_signed_alert(cert_key_pair):
    cert, key = cert_key_pair
    with pytest.raises(SSLHealthcheckError):
        check_cert_openssl(cert, key, host=HOST, no_client=False)


def test_verify_cert_bad_cert(bad_cert):
    cert, key = bad_cert
    with pytest.raises(SSLHealthcheckError):
        check_cert_openssl(cert, key, host=HOST, no_client=True)


def test_verify_cert_bad_key(bad_key):
    cert, key = bad_key
    with pytest.raises(SSLHealthcheckError):
        check_cert_openssl(cert, key, host=HOST, no_client=True)


@mock.patch('core.ssl.post_request')
def test_upload_cert(pr_mock, cert_key_pair):
    cert, key = cert_key_pair
    upload_cert(cert, key, force=False, no_client=True)
    args = pr_mock.call_args.args
    assert args[0] == 'ssl_upload'
    kwargs = pr_mock.call_args.kwargs
    assert kwargs['files']['ssl_cert'][1].name == cert
    assert kwargs['files']['ssl_key'][1].name == key
    assert kwargs['files']['json'][1] == '{"force": false}'

    upload_cert(cert, key, force=True, no_client=True)
    args = pr_mock.call_args.args
    assert args[0] == 'ssl_upload'
    kwargs = pr_mock.call_args.kwargs
    assert kwargs['files']['ssl_cert'][1].name == cert
    assert kwargs['files']['ssl_key'][1].name == key
    assert kwargs['files']['json'][1] == '{"force": true}'

    assert pr_mock.call_count == 2
