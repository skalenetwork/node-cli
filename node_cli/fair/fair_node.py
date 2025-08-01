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
from typing import cast

from node_cli.configs import DEFAULT_SKALED_BASE_PORT, RESTORE_SLEEP_TIMEOUT, SKALE_DIR
from node_cli.configs.user import SKALE_DIR_ENV_FILEPATH
from node_cli.core.docker_config import cleanup_docker_configuration
from node_cli.core.host import is_node_inited, save_env_params
from node_cli.core.node import compose_node_env, is_base_containers_alive
from node_cli.operations import (
    FairUpdateType,
    cleanup_fair_op,
    init_fair_op,
    repair_fair_op,
    restore_fair_op,
    update_fair_op,
)
from node_cli.utils.decorators import check_inited, check_not_inited, check_user
from node_cli.utils.exit_codes import CLIExitCodes
from node_cli.utils.helper import error_exit, get_request, post_request
from node_cli.utils.node_type import NodeType
from node_cli.utils.print_formatters import print_node_cmd_error, print_node_info_fair
from node_cli.utils.texts import safe_load_texts

logger = logging.getLogger(__name__)
TEXTS = safe_load_texts()

BLUEPRINT_NAME = 'fair-node'


def get_node_info_plain() -> dict:
    status, payload = get_request(blueprint=BLUEPRINT_NAME, method='info')
    node_payload: dict = cast(dict, payload)
    if status == 'ok':
        return node_payload['node']
    else:
        error_exit(payload, exit_code=CLIExitCodes.BAD_API_RESPONSE)


def get_node_info(format):
    node_info = get_node_info_plain()
    if format == 'json':
        print(node_info)
    else:
        print_node_info_fair(node_info)


@check_not_inited
def restore_fair(backup_path, env_filepath, config_only=False):
    env = compose_node_env(env_filepath, node_type=NodeType.FAIR)
    if env is None:
        return
    save_env_params(env_filepath)
    env['SKALE_DIR'] = SKALE_DIR

    restored_ok = restore_fair_op(env, backup_path, config_only=config_only)
    if not restored_ok:
        error_exit('Restore operation failed', exit_code=CLIExitCodes.OPERATION_EXECUTION_ERROR)
    time.sleep(RESTORE_SLEEP_TIMEOUT)
    print('Fair node is restored from backup')


@check_inited
@check_user
def migrate_from_boot(
    env_filepath: str,
) -> None:
    logger.info('Migrating from boot to fair node...')
    env = compose_node_env(
        env_filepath,
        inited_node=True,
        sync_schains=False,
        node_type=NodeType.FAIR,
    )
    migrate_ok = update_fair_op(env_filepath, env, update_type=FairUpdateType.FROM_BOOT)
    alive = is_base_containers_alive(node_type=NodeType.FAIR)
    if not migrate_ok or not alive:
        print_node_cmd_error()
        return
    else:
        logger.info('Migration from boot to fair completed successfully')


@check_inited
@check_user
def update(
    env_filepath: str, pull_config_for_schain: str | None = None, force_skaled_start: bool = False
) -> None:
    logger.info(
        'Updating fair node: %s, pull_config_for_schain: %s, force_skaled_start: %s',
        env_filepath,
        pull_config_for_schain,
        force_skaled_start,
    )
    env = compose_node_env(
        env_filepath,
        inited_node=True,
        sync_schains=False,
        node_type=NodeType.FAIR,
        pull_config_for_schain=pull_config_for_schain,
    )
    update_ok = update_fair_op(
        env_filepath,
        env,
        update_type=FairUpdateType.REGULAR,
        force_skaled_start=force_skaled_start,
    )
    alive = is_base_containers_alive(node_type=NodeType.FAIR)
    if not update_ok or not alive:
        print_node_cmd_error()
        return
    else:
        logger.info('Fair update completed successfully')


@check_user
def cleanup() -> None:
    env = compose_node_env(SKALE_DIR_ENV_FILEPATH, save=False, node_type=NodeType.FAIR)
    cleanup_fair_op(env)
    logger.info('Fair node was cleaned up, all containers and data removed')
    cleanup_docker_configuration()


@check_not_inited
def init(env_filepath: str) -> None:
    env = compose_node_env(env_filepath, node_type=NodeType.FAIR)
    if env is None:
        return
    save_env_params(env_filepath)
    env['SKALE_DIR'] = SKALE_DIR

    init_ok = init_fair_op(env_filepath, env)
    if not init_ok:
        error_exit('Init operation failed', exit_code=CLIExitCodes.OPERATION_EXECUTION_ERROR)
    time.sleep(RESTORE_SLEEP_TIMEOUT)
    print('Fair node is initialized')


@check_inited
@check_user
def register(ip: str) -> None:
    if not is_node_inited():
        print(TEXTS['fair']['node']['not_inited'])
        return

    json_data = {'ip': ip, 'port': DEFAULT_SKALED_BASE_PORT}
    status, payload = post_request(blueprint=BLUEPRINT_NAME, method='register', json=json_data)
    if status == 'ok':
        msg = TEXTS['fair']['node']['registered']
        logger.info(msg)
        print(msg)
    else:
        error_msg = payload
        logger.error(f'Registration error {error_msg}')
        error_exit(error_msg, exit_code=CLIExitCodes.BAD_API_RESPONSE)


def repair_chain(snapshot_from: str = 'any') -> None:
    env = compose_node_env(SKALE_DIR_ENV_FILEPATH, save=False, node_type=NodeType.FAIR)
    repair_fair_op(env=env, snapshot_from=snapshot_from)


@check_inited
@check_user
def change_ip(ip: str) -> None:
    if not is_node_inited():
        print(TEXTS['fair']['node']['not_inited'])
        return

    json_data = {'ip': ip, 'port': DEFAULT_SKALED_BASE_PORT}
    status, payload = post_request(blueprint=BLUEPRINT_NAME, method='change-ip', json=json_data)
    if status == 'ok':
        msg = TEXTS['fair']['node']['ip_changed']
        logger.info(msg)
        print(msg)
    else:
        error_msg = payload
        logger.error(f'Change IP error {error_msg}')
        error_exit(error_msg, exit_code=CLIExitCodes.BAD_API_RESPONSE)
