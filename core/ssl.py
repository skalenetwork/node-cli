import json
import time
import os
import subprocess
from contextlib import contextmanager

import logging

# from configs import SKALED_SSL_TEST_SCRIPT
from tools.helper import run_cmd
from core.helper import post_request, read_file

logger = logging.getLogger(__name__)


def load_ssl_files(key_path, cert_path):
    return {
        'ssl_key': (os.path.basename(key_path),
                    read_file(key_path), 'application/octet-stream'),
        'ssl_cert': (os.path.basename(cert_path),
                     read_file(cert_path), 'application/octet-stream')
    }


def run_simple_openssl_server(certfile, keyfile, port=33333):
    cmd = [
        'openssl', 's_server',
        '-cert', certfile,
        '-key', keyfile,
        '-WWW',
        '-port', str(port),
        '-CAfile', certfile,
        '-verify_return_error', '-Verify', '1'
    ]
    run_cmd(cmd)


@contextmanager
def detached_subprocess(cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    try:
        yield p
    finally:
        p.terminate()


class SSLServerError(Exception):
    pass


# def check_cert_skaled(cert_path, key_path):
#     run_cmd([
#         SKALED_SSL_TEST_SCRIPT,
#         '--proto=https',
#         f'--ssl-key={key_path}',
#         f'--ssl-cert={cert_path}'
#     ])


def check_cert(cert_path, key_path, port=33333, no_client=False):
    server_cmd = [
        'openssl', 's_server',
        '-cert', cert_path,
        '-key', key_path,
        '-WWW',
        '-port', str(port),
        '-verify_return_error', '-Verify', '1'
    ]
    ssl_check_cmd = [
        'openssl', 's_client',
        '-connect', f'127.0.0.1:{port}',
        '-verify_return_error'
    ]

    with detached_subprocess(server_cmd) as dp:
        time.sleep(1)
        code = dp.poll()
        if code is not None:
            raise SSLServerError('Openssl server was failed to start')
        # Connect to ssl server
        if not no_client:
            run_cmd(ssl_check_cmd)


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


def upload_certs(key_path, cert_path, force):
    try:
        check_cert(cert_path, key_path)
    except Exception as err:
        logger.exception('Cerificate/key pair is incorrect')
        return 'error', f'Certificate check failed. {err}'
    return send_saving_cert_request(key_path, cert_path, force)
