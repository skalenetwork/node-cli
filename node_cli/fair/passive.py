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

import logging

from node_cli.core.host import is_node_inited
from node_cli.utils.texts import safe_load_texts
from node_cli.utils.helper import error_exit, post_request
from node_cli.utils.exit_codes import CLIExitCodes

logger = logging.getLogger(__name__)
TEXTS = safe_load_texts()
BLUEPRINT_NAME = 'fair-node-passive'


def setup_fair_passive(node_id: int) -> None:
    if not is_node_inited():
        print(TEXTS['fair']['node']['not_inited'])
        return

    json_data = {'id': node_id}
    status, payload = post_request(blueprint=BLUEPRINT_NAME, method='setup', json=json_data)
    if status == 'ok':
        msg = TEXTS['fair']['node']['setup_complete']
        logger.info(msg)
        print(msg)
    else:
        error_msg = payload
        logger.error(f'Setup error {error_msg}')
        error_exit(error_msg, exit_code=CLIExitCodes.BAD_API_RESPONSE)
