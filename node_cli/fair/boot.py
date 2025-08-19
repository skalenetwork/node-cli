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

from node_cli.configs import TM_INIT_TIMEOUT
from node_cli.core.node import compose_node_env, is_base_containers_alive
from node_cli.core.node_options import upsert_node_mode
from node_cli.operations import init_fair_boot_op, update_fair_boot_op
from node_cli.utils.decorators import check_inited, check_not_inited, check_user
from node_cli.utils.exit_codes import CLIExitCodes
from node_cli.utils.helper import error_exit
from node_cli.utils.node_type import NodeMode, NodeType
from node_cli.utils.print_formatters import print_node_cmd_error

logger = logging.getLogger(__name__)


@check_not_inited
def init(env_filepath: str) -> None:
    node_mode = NodeMode.ACTIVE
    node_type = NodeType.FAIR
    env = compose_node_env(
        env_filepath,
        node_type=node_type,
        node_mode=node_mode,
        is_fair_boot=True,
    )

    init_fair_boot_op(env_filepath, env, node_mode)
    logger.info('Waiting for fair containers initialization')
    time.sleep(TM_INIT_TIMEOUT)
    if not is_base_containers_alive(node_type=node_type, node_mode=node_mode, is_fair_boot=True):
        error_exit('Containers are not running', exit_code=CLIExitCodes.OPERATION_EXECUTION_ERROR)
    logger.info('Init fair procedure finished')


@check_inited
@check_user
def update(env_filepath: str, pull_config_for_schain: str) -> None:
    logger.info('Fair boot node update started')
    node_mode = upsert_node_mode(node_mode=NodeMode.ACTIVE)
    env = compose_node_env(
        env_filepath,
        inited_node=True,
        sync_schains=False,
        pull_config_for_schain=pull_config_for_schain,
        node_type=NodeType.FAIR,
        node_mode=node_mode,
        is_fair_boot=True,
    )
    migrate_ok = update_fair_boot_op(env_filepath, env)
    if migrate_ok:
        logger.info('Waiting for containers initialization')
        time.sleep(TM_INIT_TIMEOUT)
    alive = is_base_containers_alive(
        node_type=NodeType.FAIR, node_mode=node_mode, is_fair_boot=True
    )
    if not migrate_ok or not alive:
        print_node_cmd_error()
        return
    else:
        logger.info('Fair boot node update finished successfully!')
