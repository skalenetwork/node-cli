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

from node_cli.configs import INIT_TIMEOUT, TM_INIT_TIMEOUT
from node_cli.core.node import compose_node_env, is_base_containers_alive
from node_cli.core.node_options import upsert_node_mode
from node_cli.fair.passive import setup_fair_passive
from node_cli.operations import (
    FairUpdateType,
    cleanup_fair_op,
    init_fair_op,
    repair_fair_op,
    turn_off_op,
    turn_on_op,
    update_fair_op,
)
from node_cli.utils.decorators import check_inited, check_not_inited, check_user
from node_cli.utils.exit_codes import CLIExitCodes
from node_cli.utils.helper import error_exit
from node_cli.utils.node_type import NodeMode, NodeType
from node_cli.utils.print_formatters import print_node_cmd_error
from node_cli.utils.settings import validate_and_save_node_settings
from node_cli.utils.texts import safe_load_texts
from skale_core.settings import get_settings

logger = logging.getLogger(__name__)
TEXTS = safe_load_texts()


@check_not_inited
def init(
    node_mode: NodeMode,
    config_file: str,
    node_id: int | None = None,
    indexer: bool = False,
    archive: bool = False,
    snapshot: str | None = None,
) -> None:
    settings = validate_and_save_node_settings(config_file, NodeType.FAIR, node_mode)
    compose_env = compose_node_env(node_type=NodeType.FAIR, node_mode=node_mode)

    init_ok = init_fair_op(
        settings=settings,
        compose_env=compose_env,
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


@check_inited
@check_user
def cleanup(node_mode: NodeMode, prune: bool = False) -> None:
    node_mode = upsert_node_mode(node_mode=node_mode)
    compose_env = compose_node_env(node_type=NodeType.FAIR, node_mode=node_mode)
    cleanup_fair_op(node_mode=node_mode, compose_env=compose_env, prune=prune)
    logger.info('Fair node was cleaned up, all containers and data removed')


@check_inited
@check_user
def update(
    node_mode: NodeMode,
    config_file: str,
    pull_config_for_schain: str | None = None,
    force_skaled_start: bool = False,
) -> None:
    logger.info(
        'Updating fair node: %s, pull_config_for_schain: %s, force_skaled_start: %s',
        config_file,
        pull_config_for_schain,
        force_skaled_start,
    )
    node_mode = upsert_node_mode(node_mode=node_mode)

    settings = validate_and_save_node_settings(config_file, NodeType.FAIR, node_mode)
    compose_env = compose_node_env(node_type=NodeType.FAIR, node_mode=node_mode)
    update_ok = update_fair_op(
        settings=settings,
        compose_env=compose_env,
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
    settings = get_settings()
    repair_fair_op(env_type=settings.env_type, snapshot_from=snapshot_from)


@check_inited
@check_user
def turn_off(node_type: NodeType) -> None:
    node_mode = upsert_node_mode()
    compose_env = compose_node_env(node_type=node_type, node_mode=node_mode)
    turn_off_op(compose_env=compose_env, node_type=node_type, node_mode=node_mode)


@check_inited
@check_user
def turn_on(env_file: str, node_type: NodeType) -> None:
    node_mode = upsert_node_mode()
    settings = validate_and_save_node_settings(env_file, node_type, node_mode)
    compose_env = compose_node_env(node_type=node_type, node_mode=node_mode)
    turn_on_op(settings=settings, compose_env=compose_env, node_type=node_type, node_mode=node_mode)
    logger.info('Waiting for containers initialization')
    time.sleep(TM_INIT_TIMEOUT)
    if not is_base_containers_alive(node_type=node_type, node_mode=node_mode):
        print_node_cmd_error()
        return
    logger.info('Node turned on')
