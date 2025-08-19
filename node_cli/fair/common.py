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

import time
import logging

from node_cli.configs import INIT_TIMEOUT, SKALE_DIR
from node_cli.configs.user import SKALE_DIR_ENV_FILEPATH
from node_cli.core.docker_config import cleanup_docker_configuration
from node_cli.core.node import compose_node_env, is_base_containers_alive
from node_cli.core.node_options import upsert_node_mode
from node_cli.fair.passive import setup_fair_passive
from node_cli.operations import (
    FairUpdateType,
    cleanup_fair_op,
    repair_fair_op,
    update_fair_op,
    init_fair_op,
)
from node_cli.core.host import save_env_params
from node_cli.utils.decorators import check_inited, check_not_inited, check_user
from node_cli.utils.node_type import NodeMode, NodeType
from node_cli.utils.print_formatters import print_node_cmd_error
from node_cli.utils.texts import safe_load_texts
from node_cli.utils.exit_codes import CLIExitCodes
from node_cli.utils.helper import error_exit

logger = logging.getLogger(__name__)
TEXTS = safe_load_texts()


@check_not_inited
def init(
    node_mode: NodeMode,
    env_filepath: str,
    node_id: int | None = None,
    indexer: bool = False,
    archive: bool = False,
    snapshot: str | None = None,
) -> None:
    env = compose_node_env(env_filepath, node_type=NodeType.FAIR, node_mode=node_mode)
    if env is None:
        return
    save_env_params(env_filepath)
    env['SKALE_DIR'] = SKALE_DIR

    init_ok = init_fair_op(
        env_filepath,
        env,
        node_mode=node_mode,
        indexer=indexer,
        archive=archive,
        snapshot=snapshot,
    )
    if not init_ok:
        error_exit('Init operation failed', exit_code=CLIExitCodes.OPERATION_EXECUTION_ERROR)
    time.sleep(INIT_TIMEOUT)

    if node_mode == NodeMode.PASSIVE and node_id is not None:
        setup_fair_passive(node_id)

    print('Fair node is initialized')


@check_user
def cleanup(node_mode: NodeMode) -> None:
    node_mode = upsert_node_mode(node_mode=node_mode)
    env = compose_node_env(
        SKALE_DIR_ENV_FILEPATH, save=False, node_type=NodeType.FAIR, node_mode=node_mode
    )
    cleanup_fair_op(node_mode=node_mode, env=env)
    logger.info('Fair node was cleaned up, all containers and data removed')
    cleanup_docker_configuration()


@check_inited
@check_user
def update(
    node_mode: NodeMode,
    env_filepath: str,
    pull_config_for_schain: str | None = None,
    force_skaled_start: bool = False,
) -> None:
    logger.info(
        'Updating fair node: %s, pull_config_for_schain: %s, force_skaled_start: %s',
        env_filepath,
        pull_config_for_schain,
        force_skaled_start,
    )
    node_mode = upsert_node_mode(node_mode=node_mode)

    env = compose_node_env(
        env_filepath,
        inited_node=True,
        sync_schains=False,
        node_type=NodeType.FAIR,
        node_mode=node_mode,
        pull_config_for_schain=pull_config_for_schain,
    )
    update_ok = update_fair_op(
        env_filepath,
        env,
        node_mode=node_mode,
        update_type=FairUpdateType.REGULAR,
        force_skaled_start=force_skaled_start,
    )
    alive = is_base_containers_alive(node_type=NodeType.FAIR, node_mode=node_mode)
    if not update_ok or not alive:
        print_node_cmd_error()
        return
    else:
        logger.info('Fair update completed successfully')


def repair_chain(snapshot_from: str = 'any') -> None:
    node_mode = upsert_node_mode()
    env = compose_node_env(
        SKALE_DIR_ENV_FILEPATH, save=False, node_type=NodeType.FAIR, node_mode=node_mode
    )
    repair_fair_op(node_mode=node_mode, env=env, snapshot_from=snapshot_from)
