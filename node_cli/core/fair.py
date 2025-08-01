#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
#
#   Copyright (C) 2019-Present SKALE Labs
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

from node_cli.utils.helper import post_request, error_exit
from node_cli.utils.exit_codes import CLIExitCodes


logger = logging.getLogger(__name__)
BLUEPRINT_NAME = 'fair'


def fair_node_exit():
    print('Removing node from fair manager contracts...')
    status, payload = post_request(blueprint=BLUEPRINT_NAME, method='node/exit')
    
    if status == 'ok':
        print('Node successfully removed from fair manager contracts')
    else:
        error_msg = payload
        logger.error(f'Fair node exit error {error_msg}')
        error_exit(error_msg, exit_code=CLIExitCodes.BAD_API_RESPONSE)