#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
#
#   Copyright (C) 2022-Present SKALE Labs
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

import time
import socket
import logging
from contextlib import contextmanager

from node_cli.core.ssl.utils import detached_subprocess
from node_cli.configs.ssl import (
    DEFAULT_SSL_CHECK_PORT,
    SKALED_SSL_TEST_SCRIPT,
    SSL_CERT_FILEPATH,
    SSL_KEY_FILEPATH
)


logger = logging.getLogger(__name__)


def check_cert(
    cert_path=SSL_CERT_FILEPATH,
    key_path=SSL_KEY_FILEPATH,
    port=DEFAULT_SSL_CHECK_PORT,
    check_type='all',
    no_client=False,
    no_wss=False
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
                host='127.0.0.1', port=port, no_wss=no_wss
            )
        except Exception as err:
            logger.exception('Certificate/key pair is incorrect for skaled')
            return 'error', f'Skaled ssl check failed. {err}'

    return 'ok', None


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
            logger.info('Healthcheck connection passed')


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


def check_cert_skaled(
    cert_path,
    key_path,
    host='127.0.0.1',
    port=DEFAULT_SSL_CHECK_PORT,
    no_wss=False
):
    run_skaled_https_healthcheck(cert_path, key_path, host, port)
    if not no_wss:
        run_skaled_wss_healthcheck(cert_path, key_path, host, port)


def run_skaled_https_healthcheck(
    cert_path,
    key_path,
    host='127.0.0.1',
    port=DEFAULT_SSL_CHECK_PORT
):
    skaled_https_check_cmd = [
        SKALED_SSL_TEST_SCRIPT,
        '--ssl-cert', cert_path,
        '--ssl-key', key_path,
        '--bind', host,
        '--port', str(port)
    ]
    with detached_subprocess(skaled_https_check_cmd, expose_output=True) as dp:
        time.sleep(1)
        code = dp.poll()
        if code is not None:
            logger.info('Skaled https check server successfully started')
        else:
            logger.error('Skaled https check server was failed to start')
            raise SSLHealthcheckError(
                'Skaled https check was failed')


def run_skaled_wss_healthcheck(
    cert_path,
    key_path,
    host='127.0.0.1',
    port=DEFAULT_SSL_CHECK_PORT
):
    skaled_wss_check_cmd = [
        SKALED_SSL_TEST_SCRIPT,
        '--ssl-cert', cert_path,
        '--ssl-key', key_path,
        '--bind', host,
        '--port', str(port),
        '--proto', 'wss',
        '--echo'
    ]

    with detached_subprocess(skaled_wss_check_cmd, expose_output=True) as dp:
        time.sleep(4)
        code = dp.poll()
        if code is not None:
            logger.error('Skaled wss check server was failed to start')
            raise SSLHealthcheckError(
                'Skaled wss check was failed')
        else:
            logger.info('Skaled wss check server successfully started')


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
