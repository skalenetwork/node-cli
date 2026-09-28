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

import os

from node_cli.configs import NODE_DATA_PATH, SGX_CERTS_PATH

# File names are fixed by the sgx client library that node services use; it expects
# exactly these three entries in the certificate directory.
SGX_KEY_FILENAME = 'sgx.key'
SGX_CSR_FILENAME = 'sgx.csr'
SGX_CRT_FILENAME = 'sgx.crt'

SGX_CERTS_BACKUP_PATH = os.path.join(NODE_DATA_PATH, 'sgx_certs_backup')

# The SGX wallet signs certificate requests over plain HTTP on the port that follows
# its main port, which is how the sgx client library derives the address as well.
SGX_CSR_SERVER_PORT_OFFSET = 1

SGX_KEY_SIZE = 2048
SGX_RPC_TIMEOUT = 60
SGX_SIGN_POLL_INTERVAL = 10
SGX_SIGN_TIMEOUT = 600
SGX_CERT_EXPIRY_WARNING_DAYS = 30

__all__ = [
    'SGX_CERTS_PATH',
    'SGX_CERTS_BACKUP_PATH',
    'SGX_CERT_EXPIRY_WARNING_DAYS',
    'SGX_CRT_FILENAME',
    'SGX_CSR_FILENAME',
    'SGX_CSR_SERVER_PORT_OFFSET',
    'SGX_KEY_FILENAME',
    'SGX_KEY_SIZE',
    'SGX_RPC_TIMEOUT',
    'SGX_SIGN_POLL_INTERVAL',
    'SGX_SIGN_TIMEOUT',
]
