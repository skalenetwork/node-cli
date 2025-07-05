#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
#
#   Copyright (C) 2025-Present SKALE Labs
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

from node_cli.utils.exit_codes import CLIExitCodes
from node_cli.utils.helper import error_exit, get_request
from node_cli.utils.print_formatters import print_wallet_info

BLUEPRINT_NAME = 'wallet'


def get_wallet_info(_format):
    status, payload = get_request(BLUEPRINT_NAME, 'mirage-info')
    if status == 'ok':
        if _format == 'json':
            print(json.dumps(payload))
        else:
            print_wallet_info(payload)
    else:
        error_exit(payload, exit_code=CLIExitCodes.BAD_API_RESPONSE)
