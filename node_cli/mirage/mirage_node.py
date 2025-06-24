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

from node_cli.configs import RESTORE_SLEEP_TIMEOUT, SKALE_DIR
from node_cli.configs.user import SKALE_DIR_ENV_FILEPATH
from node_cli.core.host import save_env_params
from node_cli.core.node import compose_node_env, is_base_containers_alive
from node_cli.mirage.record.chain_record import get_mirage_chain_record
from node_cli.operations import MirageUpdateType, restore_mirage_op, update_mirage_op
from node_cli.utils.decorators import check_inited, check_not_inited, check_user
from node_cli.utils.exit_codes import CLIExitCodes
from node_cli.utils.helper import error_exit
from node_cli.utils.node_type import NodeType
from node_cli.utils.print_formatters import print_node_cmd_error
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
@check_user
def migrate_from_boot(
    env_filepath: str,
) -> None:
    logger.info('Migrating from boot to mirage node...')
    env = compose_node_env(
        env_filepath,
        inited_node=True,
        sync_schains=False,
        node_type=NodeType.MIRAGE,
    )
    migrate_ok = update_mirage_op(env_filepath, env, update_type=MirageUpdateType.FROM_BOOT)
    alive = is_base_containers_alive(node_type=NodeType.MIRAGE)
    if not migrate_ok or not alive:
        print_node_cmd_error()
        return
    else:
        logger.info('Migration from boot to mirage completed successfully')


def request_repair(snapshot_from: str = '') -> None:
    env = compose_node_env(SKALE_DIR_ENV_FILEPATH, save=False, node_type=NodeType.MIRAGE)
    record = get_mirage_chain_record(env)
    record.set_repair_ts(int(time.time()))
    record.set_snapshot_from(snapshot_from)
    print(TEXTS['mirage']['node']['repair']['repair_requested'])
