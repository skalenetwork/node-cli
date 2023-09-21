import logging
import os
import pprint
import shutil
from pathlib import Path

from typing import Dict, Optional

from node_cli.configs import NODE_CONFIG_PATH
from node_cli.utils.helper import get_request, post_request, error_exit
from node_cli.utils.exit_codes import CLIExitCodes
from node_cli.utils.print_formatters import (
    print_dkg_statuses,
    print_firewall_rules,
    print_schain_info,
    print_schains
)
from node_cli.utils.helper import read_json, run_cmd
from lvmpy.src.core import mount, volume_mountpoint


logger = logging.getLogger(__name__)

BLUEPRINT_NAME = 'schains'


def get_schain_firewall_rules(schain: str) -> None:
    status, payload = get_request(
        blueprint=BLUEPRINT_NAME,
        method='firewall-rules',
        params={'schain_name': schain}
    )
    if status == 'ok':
        print_firewall_rules(payload['endpoints'])
    else:
        error_exit(payload, exit_code=CLIExitCodes.BAD_API_RESPONSE)


def show_schains(only_names=False) -> None:
    status, payload = get_request(
        blueprint=BLUEPRINT_NAME,
        method='list'
    )
    if status == 'ok':
        schains = payload
        if not schains:
            print('No sChains found')
            return
        if only_names:
            names = [schain['name'] for schain in schains]
            print('\n'.join(names))
        else:
            print_schains(schains)
    else:
        error_exit(payload, exit_code=CLIExitCodes.BAD_API_RESPONSE)


def show_dkg_info(all_: bool = False) -> None:
    params = {'all': all_}
    status, payload = get_request(
        blueprint=BLUEPRINT_NAME,
        method='dkg-statuses',
        params=params
    )
    if status == 'ok':
        print_dkg_statuses(payload)
    else:
        error_exit(payload, exit_code=CLIExitCodes.BAD_API_RESPONSE)


def show_config(name: str) -> None:
    status, payload = get_request(
        blueprint=BLUEPRINT_NAME,
        method='config',
        params={'schain_name': name}
    )
    if status == 'ok':
        pprint.pprint(payload)
    else:
        error_exit(payload, exit_code=CLIExitCodes.BAD_API_RESPONSE)


def toggle_schain_repair_mode(
    schain: str,
    snapshot_from: Optional[str] = None
) -> None:
    json_params = {'schain_name': schain}
    if snapshot_from:
        json_params.update({'snapshot_from': snapshot_from})
    status, payload = post_request(
        blueprint=BLUEPRINT_NAME,
        method='repair',
        json=json_params
    )
    if status == 'ok':
        print('Schain has been set for repair')
    else:
        error_exit(payload, exit_code=CLIExitCodes.BAD_API_RESPONSE)


def describe(schain: str, raw=False) -> None:
    status, payload = get_request(
        blueprint=BLUEPRINT_NAME,
        method='get',
        params={'schain_name': schain}
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


def fillin_snapshot_folder(src_path: str, block_number: int) -> None:
    snapshots_dirname = 'snapshots'
    snapshot_folder_path = os.path.join(
        src_path, snapshots_dirname, str(block_number))
    os.makedirs(snapshot_folder_path, exist_ok=True)
    for subvolume in os.listdir(src_path):
        if subvolume != snapshots_dirname:
            logger.debug('Copying %s to %s', subvolume, snapshot_folder_path)
            subvolume_path = os.path.join(src_path, subvolume)
            subvolume_snapshot_path = os.path.join(
                snapshot_folder_path, subvolume)
            make_btrfs_snapshot(subvolume_path, subvolume_snapshot_path)


def restore_schain_from_snapshot(schain: str, snapshot_path: str) -> None:
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
