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
from typing import Any, Dict

from node_cli.utils.exit_codes import CLIExitCodes
from node_cli.utils.helper import error_exit, get_request
from node_cli.utils.print_formatters import print_chain_record, print_chain_checks

BLUEPRINT_NAME = 'fair-chain'


def get_chain_record_plain() -> Dict[str, Any]:
    status, payload = get_request(blueprint=BLUEPRINT_NAME, method='record')
    if status == 'ok':
        if isinstance(payload, dict):
            return payload.get('record', {})
        else:
            error_exit('Invalid response format', exit_code=CLIExitCodes.BAD_API_RESPONSE)
    else:
        error_exit(payload, exit_code=CLIExitCodes.BAD_API_RESPONSE)


def get_chain_record(raw: bool = False) -> None:
    record = get_chain_record_plain()
    if raw:
        print(json.dumps(record, indent=4))
    else:
        print_chain_record(record)


def get_chain_checks_plain() -> Dict[str, Any]:
    status, payload = get_request(blueprint=BLUEPRINT_NAME, method='checks')
    if status == 'ok':
        if isinstance(payload, dict):
            return payload
        else:
            error_exit('Invalid response format', exit_code=CLIExitCodes.BAD_API_RESPONSE)
    else:
        error_exit(payload, exit_code=CLIExitCodes.BAD_API_RESPONSE)


def get_chain_checks(raw: bool = False) -> None:
    checks = get_chain_checks_plain()
    if raw:
        print(json.dumps(checks, indent=4))
    else:
        print_chain_checks(checks)
