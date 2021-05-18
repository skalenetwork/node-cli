import json
import os
import socket
import subprocess
import time
from contextlib import contextmanager

import logging

from configs import (
    DEFAULT_SSL_CHECK_PORT,
    SKALED_SSL_TEST_SCRIPT,
    SSL_CERT_FILEPATH,
    SSL_KEY_FILEPATH
)
from core.helper import post_request, read_file
from tools.helper import run_cmd

logger = logging.getLogger(__name__)

COMMUNICATION_TIMEOUT = 3


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
def detached_subprocess(cmd, expose_output=False):
    logger.debug(f'Starting detached subprocess: {cmd}')
    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        encoding='utf-8'
    )
    try:
        yield p
    finally:
        p.terminate()
        output = p.stdout.read()
        if expose_output:
            print(output)
        logger.debug(f'Detached process {cmd} output:\n{output}')


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


def check_ssl_connection(host, port, silent=False):
    logger.info(f'Connecting to public ssl endpoint {host}:{port} ...')
    ssl_check_cmd = [
        'openssl', 's_client',
        '-connect', f'{host}:{port}',
        '-verify_return_error', '-verify', '2'
    ]
    expose_output = not silent
    with detached_subprocess(ssl_check_cmd, expose_output=expose_output) as dp:
        time.sleep(1)
        code = dp.poll()
        if code is not None:
            logger.error('Healthcheck connection failed')
            raise SSLHealthcheckError('OpenSSL connection verification failed')


def check_cert_skaled(
    cert_path,
    key_path,
    host='127.0.0.1',
    port=DEFAULT_SSL_CHECK_PORT
):
    skaled_ssl_check_cmd = [
        SKALED_SSL_TEST_SCRIPT,
        '--ssl-cert', cert_path,
        '--ssl-key', key_path,
        '--bind', host,
        '--port', str(port)
    ]
    with detached_subprocess(skaled_ssl_check_cmd, expose_output=True) as dp:
        time.sleep(1)
        code = dp.poll()
        if code is not None:
            logger.info('Skaled ssl check server successfully started')
        else:
            logger.error('Skaled ssl check server was failed to start')
            raise SSLHealthcheckError(
                'Skaled https check was failed')


@contextmanager
def openssl_server(host, port, cert_path, key_path, silent=False):
    ssl_server_cmd = [
        'openssl', 's_server',
        '-cert', cert_path,
        '-cert_chain', cert_path,
        '-key', key_path,
        '-WWW',
        '-accept', f'{host}:{port}',
        '-verify_return_error', '-verify', '1'
    ]
    logger.info(f'Staring healthcheck server on port {port} ...')
    expose_output = not silent
    with detached_subprocess(
        ssl_server_cmd, expose_output=expose_output
    ) as dp:
        yield dp


def check_cert_openssl(
    cert_path,
    key_path,
    host='127.0.0.1',
    port=DEFAULT_SSL_CHECK_PORT,
    no_client=False,
    silent=False
):
    with openssl_server(
        host, port, cert_path,
        key_path, silent=silent
    ) as serv:
        time.sleep(1)
        code = serv.poll()
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
            check_ssl_connection(host, port, silent=silent)
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


def upload_cert(cert_path, key_path, force, no_client=False):
    try:
        check_cert_openssl(
            cert_path, key_path, silent=True, no_client=no_client)
    except Exception as err:
        logger.exception('Certificate/key pair is incorrect')
        return 'error', f'Certificate check failed. {err}'
    return send_saving_cert_request(key_path, cert_path, force)


def check_cert(
    cert_path=SSL_CERT_FILEPATH,
    key_path=SSL_KEY_FILEPATH,
    port=DEFAULT_SSL_CHECK_PORT,
    check_type='all',
    no_client=False
):
    if check_type in ('all', 'openssl'):
        try:
            check_cert_openssl(
                cert_path, key_path,
                host='127.0.0.1', port=port, no_client=no_client
            )
        except Exception as err:
            logger.exception('Cerificate/key pair is incorrect')
            return 'error', f'Certificate check failed. {err}'

    if check_type in ('all', 'skaled'):
        try:
            check_cert_skaled(
                cert_path, key_path,
                host='127.0.0.1', port=port
            )
        except Exception as err:
            logger.exception('Certificate/key pair is incorrect for skaled')
            return 'error', f'Skaled ssl check failed. {err}'

    return 'ok', None
