#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
#
#   Copyright (C) 2026 SKALE Labs
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""SGX wallet options and client certificate management.

Node services authenticate to the SGX wallet with a client certificate kept in
``node_data/sgx_certs``. The sgx client library inside the containers expects exactly
three files there (``sgx.key``, ``sgx.csr`` and ``sgx.crt``) and issues a certificate on
its own only when one of them is missing, so this module never leaves that directory
incomplete: new material is prepared next to it and moved into place with per-file
atomic renames, and the current certificate is kept until the new one is signed.
Certificate operations talk to the SGX server directly. Server options are queried
through the authenticated node API.
"""

import datetime
import logging
import os
import secrets
import shutil
import tempfile
import time
import warnings
from collections.abc import Callable
from pathlib import Path
from urllib.parse import urlparse

import requests
from cryptography import x509
from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from urllib3.exceptions import InsecureRequestWarning

from node_cli.configs.sgx import (
    SGX_CERT_EXPIRY_WARNING_DAYS,
    SGX_CERTS_BACKUP_PATH,
    SGX_CERTS_PATH,
    SGX_CRT_FILENAME,
    SGX_CSR_FILENAME,
    SGX_CSR_SERVER_PORT_OFFSET,
    SGX_KEY_FILENAME,
    SGX_KEY_SIZE,
    SGX_RPC_TIMEOUT,
    SGX_SIGN_POLL_INTERVAL,
    SGX_SIGN_TIMEOUT,
)
from node_cli.utils.helper import get_request

logger = logging.getLogger(__name__)

FILE_MODES = {'key': 0o600, 'csr': 0o644, 'crt': 0o644}
INSTALL_ORDER = ('key', 'csr', 'crt')
SIGNING_PENDING = 1

Logger = Callable[[str], None]


class SgxCertificateError(Exception):
    """Raised when the SGX client certificate cannot be read, issued or installed."""


def get_server_options() -> tuple[str, str | dict]:
    """Query SGX options through the admin API using the node's CLI credential."""
    return get_request(blueprint='info', method='sgx-options')


def certificate_paths(directory: str | Path | None = None) -> dict[str, Path]:
    directory = Path(directory or SGX_CERTS_PATH)
    return {
        'key': directory / SGX_KEY_FILENAME,
        'csr': directory / SGX_CSR_FILENAME,
        'crt': directory / SGX_CRT_FILENAME,
    }


def csr_server_url(sgx_url: str) -> str:
    """Address of the wallet's signing service, derived the way the sgx client does."""
    parsed = urlparse(sgx_url)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.port is None:
        raise SgxCertificateError(f'SGX URL must look like https://host:port, got {sgx_url!r}')
    host = f'[{parsed.hostname}]' if ':' in parsed.hostname else parsed.hostname
    return f'http://{host}:{parsed.port + SGX_CSR_SERVER_PORT_OFFSET}'


def get_certificate_status(directory: str | Path | None = None) -> dict:
    """Describe the certificate files without contacting the SGX server."""
    paths = certificate_paths(directory)
    present = {name: path.is_file() for name, path in paths.items()}
    status: dict = {
        'directory': str(paths['crt'].parent),
        'present': present,
        'complete': all(present.values()),
    }
    if not present['crt']:
        return status
    cert = _load_certificate(paths['crt'])
    now = datetime.datetime.now(datetime.timezone.utc)
    not_before = cert.not_valid_before_utc
    not_after = cert.not_valid_after_utc
    days_left = (not_after - now).days
    status.update(
        {
            'subject': _common_name(cert.subject),
            'issuer': _common_name(cert.issuer),
            'serial_number': format(cert.serial_number, 'x'),
            'not_valid_before': not_before.isoformat(timespec='seconds'),
            'not_valid_after': not_after.isoformat(timespec='seconds'),
            'days_left': days_left,
            'expired': now >= not_after,
            'not_yet_valid': now < not_before,
            'expires_soon': now < not_after and days_left < SGX_CERT_EXPIRY_WARNING_DAYS,
            'fingerprint_sha256': cert.fingerprint(hashes.SHA256()).hex(':'),
            'key_matches': _key_matches(paths['key'], cert) if present['key'] else None,
        }
    )
    return status


def check_certificate(sgx_url: str, directory: str | Path | None = None) -> str:
    """Return the SGX server version obtained while authenticating with the local files."""
    paths = certificate_paths(directory)
    missing = [name for name in ('key', 'crt') if not paths[name].is_file()]
    if missing:
        raise SgxCertificateError(
            f'Cannot check the certificate, missing files: {", ".join(missing)}'
        )
    return _server_version(sgx_url, (str(paths['crt']), str(paths['key'])))


def renew_certificate(
    sgx_url: str,
    *,
    directory: str | Path | None = None,
    backup_root: str | Path | None = None,
    timeout: int = SGX_SIGN_TIMEOUT,
    verify: bool = True,
    log: Logger | None = None,
) -> dict:
    """Issue a new client certificate and install it, keeping the current one until then.

    The new certificate is tested against the SGX server before it replaces the current
    files unless ``verify`` is off. Previous files are copied under ``backup_root``.
    """
    paths = certificate_paths(directory)
    certs_dir = paths['crt'].parent
    csr_url = csr_server_url(sgx_url)
    try:
        os.makedirs(certs_dir, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix='.sgx_certs.', dir=_staging_parent(certs_dir)))
    except OSError as err:
        raise SgxCertificateError(
            f'Cannot prepare certificate files in {certs_dir}: {err}'
        ) from err

    _say(log, 'Generating a new RSA key and certificate signing request ...')
    key_pem, csr_pem = _generate_key_and_csr()
    try:
        staged = {name: staging / path.name for name, path in paths.items()}
        _write_file(staged['key'], key_pem, FILE_MODES['key'])
        _write_file(staged['csr'], csr_pem, FILE_MODES['csr'])
        crt_pem = _request_signed_certificate(csr_url, csr_pem.decode('ascii'), timeout, log)
        _write_file(staged['crt'], crt_pem.encode('utf-8'), FILE_MODES['crt'])
        if not _key_matches(staged['key'], _load_certificate(staged['crt'])):
            raise SgxCertificateError(
                'The certificate returned by the SGX server does not match the generated key'
            )
        version = None
        if verify:
            _say(log, f'Verifying the new certificate against {sgx_url} ...')
            version = _server_version(sgx_url, (str(staged['crt']), str(staged['key'])))
            _say(log, f'SGX server (version {version}) accepted the new certificate')
        try:
            backup = _backup_existing(paths, Path(backup_root or SGX_CERTS_BACKUP_PATH))
            _install(staged, paths)
        except OSError as err:
            raise SgxCertificateError(f'Cannot install the new certificate files: {err}') from err
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    _say(log, f'Installed the new certificate in {certs_dir}')
    return {
        'backup': str(backup) if backup else None,
        'server_version': version,
        **get_certificate_status(certs_dir),
    }


def _say(log: Logger | None, message: str) -> None:
    logger.info(message)
    if log is not None:
        log(message)


def _rpc(
    url: str, method: str, params: dict | None = None, cert: tuple[str, str] | None = None
) -> dict:
    payload = {'id': 0, 'jsonrpc': '2.0', 'method': method, 'params': params or {}}
    try:
        with warnings.catch_warnings():
            # The SGX wallet presents a self-signed server certificate; node services
            # skip its verification the same way and rely on client authentication.
            warnings.simplefilter('ignore', InsecureRequestWarning)
            response = requests.post(
                url, json=payload, cert=cert, verify=False, timeout=SGX_RPC_TIMEOUT
            )
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.SSLError as err:
        raise SgxCertificateError(f'SGX server {url} rejected the TLS connection: {err}') from err
    except (requests.exceptions.RequestException, ValueError) as err:
        raise SgxCertificateError(f'Cannot call {method} on {url}: {err}') from err
    if not isinstance(data, dict):
        raise SgxCertificateError(f'{method} on {url} returned an unexpected response')
    if data.get('error'):
        error = data['error']
        message = error.get('message', error) if isinstance(error, dict) else error
        raise SgxCertificateError(f'{method} on {url} failed: {message}')
    result = data.get('result')
    if not isinstance(result, dict):
        raise SgxCertificateError(f'{method} on {url} returned an unexpected response')
    return result


def _raise_on_status(result: dict, method: str) -> None:
    if result.get('status', 0) != 0:
        message = result.get('errorMessage') or f'status {result.get("status")}'
        raise SgxCertificateError(f'SGX server refused {method}: {message}')


def _server_version(sgx_url: str, cert: tuple[str, str]) -> str:
    result = _rpc(sgx_url, 'getServerVersion', cert=cert)
    _raise_on_status(result, 'getServerVersion')
    return str(result.get('version') or 'unknown')


def _request_signed_certificate(
    csr_url: str, csr_pem: str, timeout: int, log: Logger | None
) -> str:
    result = _rpc(csr_url, 'signCertificate', {'certificate': csr_pem})
    _raise_on_status(result, 'signCertificate')
    csr_hash = result.get('hash')
    if not csr_hash:
        raise SgxCertificateError('SGX server did not return a hash for the signing request')
    _say(log, f'Signing request accepted by {csr_url}, hash: {csr_hash}')

    deadline = time.monotonic() + timeout
    waiting = False
    while True:
        result = _rpc(csr_url, 'getCertificate', {'hash': csr_hash})
        if result.get('status', 0) == 0 and result.get('cert'):
            return str(result['cert'])
        if result.get('status', 0) not in (0, SIGNING_PENDING):
            _raise_on_status(result, 'getCertificate')
        if not waiting:
            _say(
                log,
                'Waiting for the SGX server to sign the request. '
                'If the server requires manual confirmation, approve the hash above there.',
            )
            waiting = True
        if time.monotonic() >= deadline:
            raise SgxCertificateError(
                f'SGX server did not sign the request within {timeout} seconds '
                f'(request hash {csr_hash}); the current certificate is unchanged'
            )
        time.sleep(SGX_SIGN_POLL_INTERVAL)


def _generate_key_and_csr() -> tuple[bytes, bytes]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=SGX_KEY_SIZE)
    # The sgx client library names its requests after a random hex string as well.
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, secrets.token_hex(32))])
    csr = x509.CertificateSigningRequestBuilder().subject_name(subject).sign(key, hashes.SHA256())
    key_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    return key_pem, csr.public_bytes(serialization.Encoding.PEM)


def _load_certificate(path: Path) -> x509.Certificate:
    try:
        return x509.load_pem_x509_certificate(path.read_bytes())
    except (OSError, ValueError) as err:
        raise SgxCertificateError(f'Cannot read certificate {path}: {err}') from err


def _key_matches(key_path: Path, cert: x509.Certificate) -> bool:
    try:
        key = serialization.load_pem_private_key(key_path.read_bytes(), password=None)
    except (OSError, ValueError, TypeError, UnsupportedAlgorithm):
        return False
    encoding = serialization.Encoding.DER
    fmt = serialization.PublicFormat.SubjectPublicKeyInfo
    return key.public_key().public_bytes(encoding, fmt) == cert.public_key().public_bytes(
        encoding, fmt
    )


def _common_name(name: x509.Name) -> str:
    attributes = name.get_attributes_for_oid(NameOID.COMMON_NAME)
    return str(attributes[0].value) if attributes else name.rfc4514_string()


def _staging_parent(certs_dir: Path) -> Path:
    """Directory on the same filesystem as the certificates, so renames stay atomic."""
    parent = certs_dir.parent
    if certs_dir.stat().st_dev == parent.stat().st_dev:
        return parent
    return certs_dir


def _write_file(path: Path, data: bytes, mode: int) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    with os.fdopen(fd, 'wb') as target:
        os.fchmod(target.fileno(), mode)
        target.write(data)
        target.flush()
        os.fsync(target.fileno())


def _backup_existing(paths: dict[str, Path], backup_root: Path) -> Path | None:
    existing = [path for path in paths.values() if path.is_file()]
    if not existing:
        return None
    backup_root.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(backup_root, 0o700)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    destination = Path(tempfile.mkdtemp(prefix=f'{stamp}.', dir=backup_root))
    for path in existing:
        shutil.copy2(path, destination / path.name)
    return destination


def _install(staged: dict[str, Path], paths: dict[str, Path]) -> None:
    """Move the staged files over the current ones, preserving their ownership."""
    as_root = os.geteuid() == 0
    for name in INSTALL_ORDER:
        target = paths[name]
        if as_root and target.exists():
            info = target.stat()
            os.chown(staged[name], info.st_uid, info.st_gid)
        os.replace(staged[name], target)
