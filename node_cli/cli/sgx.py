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

import json

import click
from terminaltables import SingleTable

from node_cli.configs.sgx import SGX_SIGN_TIMEOUT
from node_cli.core.sgx import (
    SgxCertificateError,
    check_certificate,
    get_certificate_status,
    renew_certificate,
)
from node_cli.utils.decorators import check_inited, check_user
from node_cli.utils.exit_codes import CLIExitCodes
from node_cli.utils.helper import abort_if_false, error_exit
from node_cli.utils.settings import get_sgx_url
from node_cli.utils.texts import safe_load_texts

G_TEXTS = safe_load_texts()
TEXTS = G_TEXTS['sgx']


@click.group()
def sgx_cli():
    pass


@sgx_cli.group('sgx', help=TEXTS['help'])
def sgx():
    pass


@sgx.command('status', help=TEXTS['status']['help'])
@click.option('--json', 'json_format', is_flag=True, help=G_TEXTS['common']['json'])
@click.option('--check', is_flag=True, help=TEXTS['status']['check'])
def status(json_format: bool, check: bool) -> None:
    try:
        info = get_certificate_status()
    except SgxCertificateError as err:
        error_exit(str(err), exit_code=CLIExitCodes.OPERATION_EXECUTION_ERROR)
    check_error = None
    if check:
        try:
            info['server_version'] = check_certificate(_configured_sgx_url())
        except SgxCertificateError as err:
            check_error = str(err)
    if json_format:
        if check_error:
            info['check_error'] = check_error
        print(json.dumps(info))
    else:
        print_certificate_status(info)
    if check_error:
        error_exit(check_error, exit_code=CLIExitCodes.OPERATION_EXECUTION_ERROR)


@sgx.command('renew', help=TEXTS['renew']['help'])
@click.option(
    '--yes',
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt=TEXTS['renew']['prompt'],
)
@click.option(
    '--timeout',
    type=int,
    default=SGX_SIGN_TIMEOUT,
    show_default=True,
    help=TEXTS['renew']['timeout'],
)
@click.option('--skip-verify', is_flag=True, help=TEXTS['renew']['skip_verify'])
@check_inited
@check_user
def renew(timeout: int, skip_verify: bool) -> None:
    sgx_url = _configured_sgx_url()
    try:
        result = renew_certificate(sgx_url, timeout=timeout, verify=not skip_verify, log=print)
    except SgxCertificateError as err:
        error_exit(str(err), exit_code=CLIExitCodes.OPERATION_EXECUTION_ERROR)
    print_certificate_status(result)
    if result['backup']:
        print(TEXTS['renew']['backup'].format(path=result['backup']))
    print(TEXTS['renew']['done'])


def _configured_sgx_url() -> str:
    try:
        sgx_url = get_sgx_url()
    except Exception as err:  # settings files are missing or invalid
        error_exit(f'Cannot read node settings: {err}', exit_code=CLIExitCodes.NODE_STATE_ERROR)
    if not sgx_url:
        error_exit(TEXTS['no_sgx'], exit_code=CLIExitCodes.NODE_STATE_ERROR)
    return sgx_url


def print_certificate_status(info: dict) -> None:
    present = info['present']
    rows = [
        ['SGX client certificate', ''],
        ['Directory', info['directory']],
        ['Private key', _presence(present['key'])],
        ['Signing request', _presence(present['csr'])],
        ['Certificate', _presence(present['crt'])],
    ]
    if 'subject' in info:
        rows.extend(
            [
                ['Subject CN', info['subject']],
                ['Issuer CN', info['issuer']],
                ['Valid from', info['not_valid_before']],
                ['Valid until', info['not_valid_after']],
                ['Days left', str(info['days_left'])],
                ['SHA-256', info['fingerprint_sha256']],
                ['Key matches', _yes_no(info['key_matches'])],
            ]
        )
    if info.get('server_version'):
        rows.append(['SGX server', f'accepted the certificate, version {info["server_version"]}'])
    print(SingleTable(rows).table)
    for notice in _notices(info):
        print(notice)


def _notices(info: dict) -> list[str]:
    notices = []
    if not info['complete']:
        notices.append(TEXTS['status']['missing'])
    elif info.get('expired'):
        notices.append(TEXTS['status']['expired'])
    elif info.get('expires_soon'):
        notices.append(TEXTS['status']['expires_soon'].format(days=info['days_left']))
    if info.get('key_matches') is False:
        notices.append(TEXTS['status']['key_mismatch'])
    return notices


def _presence(present: bool) -> str:
    return 'present' if present else 'missing'


def _yes_no(value: bool | None) -> str:
    if value is None:
        return 'unknown'
    return 'yes' if value else 'no'
