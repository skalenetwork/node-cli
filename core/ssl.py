import json
import time
import os
import socket
import subprocess
from contextlib import contextmanager

import logging

from configs import (
    DEFAULT_SSL_CHECK_PORT,
    SSL_CERT_FILEPATH,
    SSL_KEY_FILEPATH
)
from core.core import NodeStatuses
from core.helper import get_request, post_request, read_file
from tools.helper import run_cmd

logger = logging.getLogger(__name__)


def load_ssl_files(key_path, cert_path):
    return {
        'ssl_key': (os.path.basename(key_path),
                    read_file(key_path), 'application/octet-stream'),
        'ssl_cert': (os.path.basename(cert_path),
                     read_file(cert_path), 'application/octet-stream')
    }


def run_simple_openssl_server(certfile, keyfile, port=DEFAULT_SSL_CHECK_PORT):
    cmd = [
        'openssl', 's_server',
        '-cert', certfile,
        '-key', keyfile,
        '-WWW',
        '-port', str(port),
        '-verify_return_error', '-Verify', '1'
    ]
    run_cmd(cmd)


@contextmanager
def detached_subprocess(cmd):
    logger.debug(f'Starting detached subprocess: {cmd}')
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        yield p
    finally:
        p.terminate()


class SSLHealthcheckError(Exception):
    pass


def check_endpoint(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        result = sock.connect_ex((host, port))
        logger.info('Checking healthcheck endpoint ...')
        if result != 0:
            logger.error('Port is closed')
            return False
        return True


def check_ssl_connection(host, port):
    logger.info(f'Connecting to public ssl endpoint {host}:{port} ...')
    ssl_check_cmd = [
        'openssl', 's_client',
        '-connect', f'{host}:{port}',
        '-verify_return_error'
    ]
    with detached_subprocess(ssl_check_cmd) as dp:
        time.sleep(1)
        code = dp.poll()
        if code is not None:
            logger.error('Healthcheck connection failed')
            raise SSLHealthcheckError('OpenSSL verification failed')


def check_cert(
    cert_path,
    key_path,
    host='127.0.0.1',
    port=DEFAULT_SSL_CHECK_PORT,
    no_client=True, no_skaled=True
):
    ssl_server_cmd = [
        'openssl', 's_server',
        '-cert', cert_path,
        '-key', key_path,
        '-WWW',
        '-accept', f'0.0.0.0:{port}',
        '-verify_return_error', '-Verify', '1'
    ]
    logger.info(f'Staring healthcheck server on port {port} ...')
    with detached_subprocess(ssl_server_cmd) as dp:
        time.sleep(1)
        code = dp.poll()
        if code is not None:
            logger.error('Healthcheck server failed to start')
            raise SSLHealthcheckError('OpenSSL server was failed to start')

        logger.info('Server successfully started')

        # Connect to ssl server
        if not no_client:
            if not check_endpoint(host, port):
                raise SSLHealthcheckError(
                    f'Healthcheck port is closed on {host}:{port}'
                )
            check_ssl_connection(host, port)
            logger.error('Healthcheck connection passed')


def send_saving_cert_request(key_path, cert_path, force):
    with open(key_path, 'rb') as key_file, open(cert_path, 'rb') as cert_file:
        files_data = {
            'ssl_key': (os.path.basename(key_path), key_file,
                        'application/octet-stream'),
            'ssl_cert': (os.path.basename(cert_path), cert_file,
                         'application/octet-stream')
        }
        files_data['json'] = (
            None, json.dumps({'force': force}),
            'application/json'
        )
        return post_request('ssl_upload', files=files_data)


def upload_cert(cert_path, key_path, force):
    try:
        check_cert(cert_path, key_path, no_client=True, no_skaled=True)
    except Exception as err:
        logger.exception('Certificate/key pair is incorrect')
        return 'error', f'Certificate check failed. {err}'
    return send_saving_cert_request(key_path, cert_path, force)


def check_uploaded_cert(port, no_client=False, no_skaled=False):
    # TODO: Add corresponding cli command
    status, payload = get_request('node_info')
    if status == 'error':
        return 'error', 'Request for node info failed'
    if payload['node_info']['status'] == NodeStatuses.NOT_CREATED:
        return 'error', 'Node is not registered. ' \
                        'You should do < skale node register > first'
    host = payload['node_info']['domain_name']
    try:
        check_cert(
            SSL_CERT_FILEPATH, SSL_KEY_FILEPATH,
            host=host, port=port,
            no_client=False, no_skaled=False
        )
    except Exception as err:
        logger.exception('Cerificate/key pair is incorrect')
        return 'error', f'Certificate check failed. {err}'
    return 'ok', None
