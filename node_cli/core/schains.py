#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
#
#   Copyright (C) 2025 SKALE Labs
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

import glob
import logging
import os
import pprint
import shutil
import time
from pathlib import Path
from typing import Dict, Optional

from lvmpy.src.core import mount, volume_mountpoint
from node_cli.configs import (
    ALLOCATION_FILEPATH,
    NODE_CLI_STATUS_FILENAME,
    NODE_CONFIG_PATH,
    SCHAIN_NODE_DATA_PATH,
    SCHAINS_MNT_DIR_SINGLE_CHAIN,
)
from node_cli.configs.user import get_validated_user_config
from node_cli.utils.docker_utils import ensure_volume, is_volume_exists
from node_cli.utils.exit_codes import CLIExitCodes
from node_cli.utils.helper import (
    error_exit,
    get_request,
    read_json,
    run_cmd,
    safe_load_yml,
    save_json,
)
from node_cli.utils.node_type import NodeType
from node_cli.utils.print_formatters import (
    print_dkg_statuses,
    print_firewall_rules,
    print_schain_info,
    print_schains,
)

logger = logging.getLogger(__name__)

BLUEPRINT_NAME = 'schains'


class NoDataDirForChainError(Exception):
    """Raised when no data directory is found"""

    pass


def get_schain_firewall_rules(schain: str) -> None:
    status, payload = get_request(
        blueprint=BLUEPRINT_NAME, method='firewall-rules', params={'schain_name': schain}
    )
    if status == 'ok':
        print_firewall_rules(payload['endpoints'])
    else:
        error_exit(payload, exit_code=CLIExitCodes.BAD_API_RESPONSE)


def show_schains() -> None:
    status, payload = get_request(blueprint=BLUEPRINT_NAME, method='list')
    if status == 'ok':
        schains = payload
        if not schains:
            print('No sChains found')
            return
        else:
            print_schains(schains)
    else:
        error_exit(payload, exit_code=CLIExitCodes.BAD_API_RESPONSE)


def show_dkg_info(all_: bool = False) -> None:
    params = {'all': all_}
    status, payload = get_request(blueprint=BLUEPRINT_NAME, method='dkg-statuses', params=params)
    if status == 'ok':
        print_dkg_statuses(payload)
    else:
        error_exit(payload, exit_code=CLIExitCodes.BAD_API_RESPONSE)


def show_config(name: str) -> None:
    status, payload = get_request(
        blueprint=BLUEPRINT_NAME, method='config', params={'schain_name': name}
    )
    if status == 'ok':
        pprint.pprint(payload)
    else:
        error_exit(payload, exit_code=CLIExitCodes.BAD_API_RESPONSE)


def get_node_cli_schain_status_filepath(schain_name: str) -> str:
    return os.path.join(SCHAIN_NODE_DATA_PATH, schain_name, NODE_CLI_STATUS_FILENAME)


def update_node_cli_schain_status(
    schain_name: str, repair_ts: Optional[int] = None, snapshot_from: Optional[str] = None
) -> None:
    path = get_node_cli_schain_status_filepath(schain_name)
    if os.path.isdir(path):
        orig_status = get_node_cli_schain_status(schain_name=schain_name)
        orig_status.update({'repair_ts': repair_ts, 'snapshot_from': snapshot_from})
        status = orig_status
    else:
        status = {
            'schain_name': schain_name,
            'repair_ts': repair_ts,
            'snapshot_from': snapshot_from,
        }
        os.makedirs(os.path.dirname(path), exist_ok=True)
    save_json(path, status)


def get_node_cli_schain_status(schain_name: str) -> dict:
    path = get_node_cli_schain_status_filepath(schain_name)
    return read_json(path)


def toggle_schain_repair_mode(schain: str, snapshot_from: Optional[str] = None) -> None:
    ts = int(time.time())
    update_node_cli_schain_status(schain_name=schain, repair_ts=ts, snapshot_from=snapshot_from)
    print('Schain has been set for repair')


def describe(schain: str, raw=False) -> None:
    status, payload = get_request(
        blueprint=BLUEPRINT_NAME, method='get', params={'schain_name': schain}
    )
    if status == 'ok':
        print_schain_info(payload, raw=raw)
    else:
        error_exit(payload, exit_code=CLIExitCodes.BAD_API_RESPONSE)


def btrfs_set_readonly_false(subvolume_path: str) -> None:
    run_cmd(['btrfs', 'property', 'set', '-ts', subvolume_path, 'ro', 'false'])


def btrfs_receive_binary(src_path: str, binary_path: str) -> None:
    run_cmd(['btrfs', 'receive', '-f', binary_path, src_path])


def get_block_number_from_path(snapshot_path: str) -> int:
    stem = Path(snapshot_path).stem
    bn = -1
    try:
        bn = int(stem.split('-')[-1])
    except ValueError:
        return -1
    return bn


def get_node_config() -> Dict:
    return read_json(NODE_CONFIG_PATH)


def get_node_id() -> int:
    info = get_node_config()
    return info['node_id']


def migrate_prices_and_blocks(path: str, node_id: int) -> None:
    db_suffix = '.db'
    for sname in os.listdir(path):
        subvolume_path = os.path.join(path, sname)
        logger.debug('Processing %s', sname)
        btrfs_set_readonly_false(subvolume_path)
        if sname.endswith(db_suffix):
            subvolume_path = os.path.join(path, sname)
            dbname = sname.split('_')[0]
            new_path = os.path.join(path, f'{dbname}_{node_id}{db_suffix}')
            logger.debug('New path for %s %s', sname, new_path)
            shutil.move(subvolume_path, new_path)


def make_btrfs_snapshot(src: str, dst: str) -> None:
    run_cmd(['btrfs', 'subvolume', 'snapshot', src, dst])


def rm_btrfs_subvolume(subvolume: str) -> None:
    run_cmd(['btrfs', 'subvolume', 'delete', subvolume])


def fillin_snapshot_folder(src_path: str, block_number: int) -> None:
    snapshots_dirname = 'snapshots'
    snapshot_folder_path = os.path.join(src_path, snapshots_dirname, str(block_number))
    os.makedirs(snapshot_folder_path, exist_ok=True)
    for subvolume in os.listdir(src_path):
        if subvolume != snapshots_dirname:
            logger.debug('Copying %s to %s', subvolume, snapshot_folder_path)
            subvolume_path = os.path.join(src_path, subvolume)
            subvolume_snapshot_path = os.path.join(snapshot_folder_path, subvolume)
            make_btrfs_snapshot(subvolume_path, subvolume_snapshot_path)


def restore_schain_from_snapshot(
    schain: str,
    snapshot_path: str,
    node_type: NodeType,
    env_type: Optional[str] = None,
    schain_type: str = 'medium',
) -> None:
    if env_type is None:
        user_config = get_validated_user_config(node_type=node_type)
        env_type = user_config.env_type
    ensure_schain_volume(schain, schain_type, env_type)
    block_number = get_block_number_from_path(snapshot_path)
    if block_number == -1:
        logger.error('Invalid snapshot path format')
        return
    node_id = get_node_id()

    mount(schain)
    src_path = volume_mountpoint(schain)
    logger.info('Unpacking binary')
    btrfs_receive_binary(src_path, snapshot_path)
    logger.info('Migrating suvolumes')
    migrate_prices_and_blocks(src_path, node_id)
    migrate_prices_and_blocks(src_path, node_id)
    logger.info('Recreating snapshot folder')
    fillin_snapshot_folder(src_path, block_number)


def get_schains_by_artifacts() -> str:
    return '\n'.join(os.listdir(SCHAIN_NODE_DATA_PATH))


def get_schain_volume_size(schain_type: str, env_type: str) -> int:
    alloc = safe_load_yml(ALLOCATION_FILEPATH)
    return alloc[env_type]['disk'][schain_type]


def ensure_schain_volume(schain: str, schain_type: str, env_type: str) -> None:
    if not is_volume_exists(schain):
        size = get_schain_volume_size(schain_type, env_type)
        ensure_volume(schain, size)
    else:
        logger.warning('Volume %s already exists', schain)


def cleanup_datadir_for_single_chain_node(
    chain_name: str = '', base_path: str = SCHAINS_MNT_DIR_SINGLE_CHAIN
) -> None:
    if not chain_name:
        folders = [f for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f))]
        if not folders:
            raise NoDataDirForChainError(
                f'No data directory found in {base_path}. Please check the path or specify a chain name.'
            )
        chain_name = folders[0]
    base_path = os.path.join(base_path, chain_name)
    regular_folders_pattern = f'{base_path}/[!snapshots]*'
    logger.info('Removing regular folders')
    for filepath in glob.glob(regular_folders_pattern):
        if os.path.isdir(filepath):
            logger.debug('Removing recursively %s', filepath)
            shutil.rmtree(filepath)
        if os.path.isfile(filepath):
            os.remove(filepath)

    logger.info('Removing subvolumes')
    subvolumes_pattern = f'{base_path}/snapshots/*/*'
    for filepath in glob.glob(subvolumes_pattern):
        logger.debug('Deleting subvolume %s', filepath)
        if os.path.isdir(filepath):
            rm_btrfs_subvolume(filepath)
        else:
            os.remove(filepath)
    logger.info('Cleaning up snapshots folder')
    if os.path.isdir(base_path):
        shutil.rmtree(base_path)
