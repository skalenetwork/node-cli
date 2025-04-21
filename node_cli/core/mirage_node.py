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
import time

from node_cli.configs import SKALE_DIR, RESTORE_SLEEP_TIMEOUT
from node_cli.core.host import save_env_params
from node_cli.core.node import compose_node_env
from node_cli.utils.decorators import check_not_inited
from node_cli.utils.exit_codes import CLIExitCodes
from node_cli.utils.helper import error_exit
from node_cli.utils.node_type import NodeType
from node_cli.utils.texts import Texts
from node_cli.operations import restore_mirage_op


logger = logging.getLogger(__name__)
TEXTS = Texts()


@check_not_inited
def restore_mirage(backup_path, env_filepath, config_only=False):
    env = compose_node_env(env_filepath, node_type=NodeType.MIRAGE)
    if env is None:
        return
    save_env_params(env_filepath)
    env['SKALE_DIR'] = SKALE_DIR

    restored_ok = restore_mirage_op(env, backup_path, config_only=config_only)
    if not restored_ok:
        error_exit('Restore operation failed', exit_code=CLIExitCodes.OPERATION_EXECUTION_ERROR)
    time.sleep(RESTORE_SLEEP_TIMEOUT)
    print('Mirage node is restored from backup')
