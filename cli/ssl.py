#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
#
#   Copyright (C) 2019 SKALE Labs
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

import click
from terminaltables import SingleTable

from configs import DEFAULT_SSL_CHECK_PORT, SSL_CERT_FILEPATH, SSL_KEY_FILEPATH
from core.helper import (
    get_request,
    print_err_response,
    safe_load_texts
)
from core.ssl import check_cert, upload_cert


TEXTS = safe_load_texts()


@click.group()
def ssl_cli():
    pass


@ssl_cli.group('ssl', help="sChains SSL commands")
def ssl():
    pass


@ssl.command(help="Status of the SSL certificates on the node")
def status():
    status, payload = get_request('ssl_status')
    if status == 'ok':
        if payload.get('is_empty'):
            print(TEXTS['ssl']['no_cert'])
        else:
            table_data = [
                ['Issued to', payload['issued_to']],
                ['Expiration date', payload['expiration_date']]
            ]
            table = SingleTable(table_data)
            print('SSL certificates status:')
            print(table.table)
    else:
        print_err_response(payload)


@ssl.command(help="Upload new SSL certificates")
@click.option(
    '--key-path', '-k',
    prompt="Enter path to the key file",
    help='Path to the key file'
)
@click.option(
    '--cert-path', '-c',
    prompt="Enter path to the certificate file",
    help='Path to the certificate file'
)
@click.option('--force', '-f', is_flag=True,
              help='Overwrite existing certificates')
def upload(key_path, cert_path, force):
    status, payload = upload_cert(cert_path, key_path, force)
    if status == 'ok':
        print(TEXTS['ssl']['uploaded'])
    else:
        print_err_response(payload)


@ssl.command(help="Check certificates")
@click.option(
    '--key-path', '-k',
    help='Path to the key file',
    default=SSL_KEY_FILEPATH
)
@click.option(
    '--cert-path', '-c',
    help='Path to the certificate file',
    default=SSL_CERT_FILEPATH
)
@click.option(
    '--port', '-p',
    help='Port to start ssl healtcheck server',
    type=int,
    default=DEFAULT_SSL_CHECK_PORT
)
@click.option(
    '--type', '-t',
    'type_',
    help='Check type',
    type=click.Choice(['all', 'openssl', 'skaled']),
    default='all'
)
@click.option(
    '--no-client',
    is_flag=True,
    help='Skip client connection for openssl check'
)
@click.option(
    '--no-wss',
    is_flag=True,
    help='Skip wss server starting for skaled check'
)
def check(key_path, cert_path, port, no_client, type_, no_wss):
    status, payload = check_cert(
        cert_path,
        key_path,
        port=port,
        check_type=type_,
        no_client=no_client,
        no_wss=no_wss
    )
    if status == 'ok':
        print(TEXTS['ssl']['check_passed'])
    else:
        print_err_response(payload)
