"""Test double for the SGX wallet ports used by the SGX certificate commands."""

import datetime
import hashlib
from pathlib import Path

import requests
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from node_cli.core import sgx

SGX_URL = 'https://127.0.0.1:1026'
ONE_DAY = datetime.timedelta(days=1)


def _response(result: dict) -> dict:
    return {'id': 0, 'jsonrpc': '2.0', 'result': result}


def _pem(obj) -> bytes:
    return obj.public_bytes(serialization.Encoding.PEM)


def _fingerprint(cert: x509.Certificate) -> bytes:
    return cert.fingerprint(hashes.SHA256())


class FakeSgxWallet:
    """Serves the CSR signing port and the main port of an SGX wallet through requests_mock.

    The main port emulates TLS client authentication: it only answers when the presented
    certificate was issued by this wallet and matches the presented key.
    """

    def __init__(
        self,
        mock,
        sgx_url: str = SGX_URL,
        *,
        pending_polls: int = 0,
        sign_error: str | None = None,
        reject_clients: bool = False,
        wrong_key: bool = False,
        version: str = '1.83.0',
    ):
        self.sgx_url = sgx_url
        self.pending_polls = pending_polls
        self.sign_error = sign_error
        self.reject_clients = reject_clients
        self.wrong_key = wrong_key
        self.version = version
        self.ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'sgx-wallet-ca')])
        self.calls: list[tuple[str, str]] = []
        self.client_certs: list[tuple[str, str]] = []
        self.pending: dict[str, x509.CertificateSigningRequest] = {}
        self.issued: list[x509.Certificate] = []
        mock.post(sgx_url.rstrip('/') + '/', json=self._main_port)
        mock.post(sgx.csr_server_url(sgx_url) + '/', json=self._csr_port)

    @property
    def last_issued(self) -> x509.Certificate:
        return self.issued[-1]

    def issue_files(self, directory: Path) -> None:
        """Write a valid key, request and certificate the way node services would have."""
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'ab' * 32)])
        csr = (
            x509.CertificateSigningRequestBuilder().subject_name(subject).sign(key, hashes.SHA256())
        )
        cert = self._sign(csr)
        directory.mkdir(parents=True, exist_ok=True)
        key_pem = key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
        (directory / 'sgx.key').write_bytes(key_pem)
        (directory / 'sgx.csr').write_bytes(_pem(csr))
        (directory / 'sgx.crt').write_bytes(_pem(cert))

    def _sign(self, csr: x509.CertificateSigningRequest, public_key=None) -> x509.Certificate:
        now = datetime.datetime.now(datetime.timezone.utc)
        cert = (
            x509.CertificateBuilder()
            .subject_name(csr.subject)
            .issuer_name(self.ca_name)
            .public_key(public_key or csr.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - ONE_DAY)
            .not_valid_after(now + 365 * ONE_DAY)
            .sign(self.ca_key, hashes.SHA256())
        )
        self.issued.append(cert)
        return cert

    def _csr_port(self, request, context):
        body = request.json()
        method = body['method']
        self.calls.append(('csr', method))
        if method == 'signCertificate':
            if self.sign_error:
                return _response({'status': 1, 'errorMessage': self.sign_error})
            csr_pem = body['params']['certificate']
            csr = x509.load_pem_x509_csr(csr_pem.encode())
            assert csr.is_signature_valid
            digest = hashlib.sha256(csr_pem.encode()).hexdigest()
            self.pending[digest] = csr
            return _response({'status': 0, 'hash': digest})
        if method == 'getCertificate':
            csr = self.pending[body['params']['hash']]
            if self.pending_polls > 0:
                self.pending_polls -= 1
                return _response(
                    {'status': 1, 'cert': '', 'errorMessage': 'Certificate is not signed yet'}
                )
            public_key = None
            if self.wrong_key:
                public_key = rsa.generate_private_key(65537, 2048).public_key()
            cert = self._sign(csr, public_key)
            return _response({'status': 0, 'cert': _pem(cert).decode()})
        raise AssertionError(f'Unexpected method on the CSR port: {method}')

    def _main_port(self, request, context):
        body = request.json()
        self.calls.append(('sgx', body['method']))
        assert request.verify is False
        self.client_certs.append(request.cert)
        crt_path, key_path = request.cert
        cert = x509.load_pem_x509_certificate(Path(crt_path).read_bytes())
        key = serialization.load_pem_private_key(Path(key_path).read_bytes(), password=None)
        known = {_fingerprint(issued) for issued in self.issued}
        if (
            self.reject_clients
            or _fingerprint(cert) not in known
            or key.public_key().public_numbers() != cert.public_key().public_numbers()
        ):
            raise requests.exceptions.SSLError('tlsv1 alert unknown ca')
        if body['method'] == 'getServerVersion':
            return _response({'status': 0, 'version': self.version})
        raise AssertionError(f'Unexpected method on the main port: {body["method"]}')
