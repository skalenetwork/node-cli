import logging
import os
import pprint
import shutil
import time
from pathlib import Path

from typing import Dict, Optional

from node_cli.configs import (
    ALLOCATION_FILEPATH,
    NODE_CONFIG_PATH,
    SCHAIN_NODE_DATA_PATH
)
from node_cli.configs.env import get_env_config

from node_cli.utils.helper import (
    get_request,
    error_exit,
    safe_load_yml
)
from node_cli.utils.exit_codes import CLIExitCodes
from node_cli.utils.print_formatters import (
    print_dkg_statuses,
    print_firewall_rules,
    print_schain_info,
    print_schains
)
from node_cli.utils.docker_utils import ensure_volume, is_volume_exists
from node_cli.utils.helper import read_json, run_cmd, save_json
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


def show_schains() -> None:
    status, payload = get_request(
        blueprint=BLUEPRINT_NAME,
        method='list'
    )
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


def get_node_cli_schain_status_filepath(schain_name: str) -> str:
    return os.path.join(SCHAIN_NODE_DATA_PATH, schain_name, 'node-cli.status')


def update_node_cli_schain_status(schain_name: str, status: dict) -> None:
    path = get_node_cli_schain_status_filepath(schain_name)
    save_json(path, status)


def toggle_schain_repair_mode(
    schain: str,
    snapshot_from: Optional[str] = None
) -> None:
    ts = int(time.time())
    status = {'schain_name': schain, 'repair_ts': ts}
    if snapshot_from:
        status.update({'snapshot_from': snapshot_from})
    update_node_cli_schain_status(schain, status)
    print('Schain has been set for repair')


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


def restore_schain_from_snapshot(
    schain: str,
    snapshot_path: str,
    env_type: Optional[str] = None,
    schain_type: str = 'medium'
) -> None:
    if env_type is None:
        env_config = get_env_config()
        env_type = env_config['ENV_TYPE']
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
