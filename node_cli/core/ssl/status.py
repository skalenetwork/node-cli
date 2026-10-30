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

import logging

from cryptography import x509
from cryptography.x509.oid import NameOID

from node_cli.core.ssl.utils import is_ssl_folder_empty, cert_from_file
from node_cli.configs.ssl import SSL_CERT_FILEPATH, CERTS_INVALID_FORMAT
from node_cli.utils.helper import ok_result, err_result

logger = logging.getLogger(__name__)


def cert_status():
    if is_ssl_folder_empty():
        return ok_result({'is_empty': True})

    cert = cert_from_file(SSL_CERT_FILEPATH)
    status, info = get_cert_info(cert)
    if status == 'error':
        return err_result(CERTS_INVALID_FORMAT)
    else:
        return ok_result(
            payload={'issued_to': info['issued_to'], 'expiration_date': info['expiration_date']}
        )


def get_cert_info(cert):
    try:
        crypto_cert = x509.load_pem_x509_certificate(cert)
        common_names = crypto_cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
        issued_to = common_names[0].value if common_names else None
        expiration_date = crypto_cert.not_valid_after_utc.strftime('%Y-%m-%dT%H:%M:%S')
    except Exception as err:
        logger.exception('Error during parsing certs')
        return err_result(str(err))
    return ok_result({'issued_to': issued_to, 'expiration_date': expiration_date})
