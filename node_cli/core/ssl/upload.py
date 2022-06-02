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
from node_cli.configs.ssl import CERTS_UPLOADED_ERR_MSG

from node_cli.core.ssl.check import check_cert_openssl
from node_cli.core.ssl.utils import is_ssl_folder_empty, save_cert_key_pair
from node_cli.utils.helper import ok_result

logger = logging.getLogger(__name__)


def upload_cert(cert_path, key_path, force, no_client=False):
    try:
        check_cert_openssl(
            cert_path, key_path, silent=True, no_client=no_client)
    except Exception as err:
        logger.exception('Certificate/key pair is incorrect')
        return 'error', f'Certificate check failed. {err}'
    if not is_ssl_folder_empty() and not force:
        return 'error', CERTS_UPLOADED_ERR_MSG
    save_cert_key_pair(key_path, cert_path)
    return ok_result()
