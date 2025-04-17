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
from node_cli.core.resources import update_resource_allocation
from node_cli.core.node import NodeTypes, compose_node_env, is_base_containers_alive
from node_cli.operations import init_mirage_boot_op, migrate_mirage_boot_op
from node_cli.utils.decorators import check_not_inited, check_inited, check_user
from node_cli.utils.exit_codes import CLIExitCodes
from node_cli.utils.helper import error_exit
from node_cli.utils.print_formatters import print_node_cmd_error
from node_cli.utils.texts import Texts


logger = logging.getLogger(__name__)
TEXTS = Texts()


@check_not_inited
def init(env_filepath: str) -> None:
    env = compose_node_env(
        env_filepath,
        node_type=NodeTypes.MIRAGE,
        is_mirage_boot=True,
    )

    init_mirage_boot_op(env_filepath, env)
    logger.info('Waiting for mirage containers initialization')
    time.sleep(TM_INIT_TIMEOUT)
    if not is_base_containers_alive(NodeTypes.MIRAGE):
        error_exit('Containers are not running', exit_code=CLIExitCodes.OPERATION_EXECUTION_ERROR)
    logger.info('Generating mirage resource allocation file ...')
    update_resource_allocation(env['ENV_TYPE'])
    logger.info('Init mirage procedure finished')


@check_inited
@check_user
def migrate(env_filepath: str, pull_config_for_schain: str, unsafe_ok: bool = False) -> None:
    logger.info('Node update started')
    env = compose_node_env(
        env_filepath,
        inited_node=True,
        sync_schains=False,
        pull_config_for_schain=pull_config_for_schain,
        node_type=NodeTypes.MIRAGE,
    )
    migrate_ok = migrate_mirage_boot_op(env_filepath, env)
    if migrate_ok:
        logger.info('Waiting for containers initialization')
        time.sleep(TM_INIT_TIMEOUT)
    alive = is_base_containers_alive(node_type=NodeTypes.MIRAGE)
    if not migrate_ok or not alive:
        print_node_cmd_error()
        return
    else:
        logger.info('Node migration from Mirage Boot to Mirage Main finished successfully!')
