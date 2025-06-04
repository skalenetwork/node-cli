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
from node_cli.configs.env import SKALE_DIR_ENV_FILEPATH
from node_cli.core.node import compose_node_env
from node_cli.core.host import save_env_params
from node_cli.core.static_config import get_static_params
from node_cli.mirage.record.chain_record import ChainRecord
from node_cli.operations import restore_mirage_op
from node_cli.utils.decorators import check_inited, check_not_inited
from node_cli.utils.exit_codes import CLIExitCodes
from node_cli.utils.helper import error_exit
from node_cli.utils.node_type import NodeType
from node_cli.utils.texts import safe_load_texts


logger = logging.getLogger(__name__)
TEXTS = safe_load_texts()


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


@check_inited
def toggle_mirage_repair(snapshot_from: str | None = None) -> None:
    node_type = NodeType.MIRAGE
    env = compose_node_env(SKALE_DIR_ENV_FILEPATH, save=False, node_type=node_type)
    params = get_static_params(node_type, env['ENV_TYPE'])
    record = ChainRecord(params['info']['chain_name'])
    record.set_repair_ts(int(time.time()))
    if snapshot_from:
        record.set_snapshot_from(snapshot_from)

    print(TEXTS['mirage']['toggle_repair'])
