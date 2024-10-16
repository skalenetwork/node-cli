import os
import datetime
from unittest import mock
from pathlib import Path


import freezegun

from node_cli.core.schains import cleanup_sync_datadir, toggle_schain_repair_mode
from node_cli.utils.helper import read_json


CURRENT_TIMESTAMP = 1594903080
CURRENT_DATETIME = datetime.datetime.utcfromtimestamp(CURRENT_TIMESTAMP)


@freezegun.freeze_time(CURRENT_DATETIME)
def test_toggle_repair_mode(tmp_schains_dir):
    schain_name = 'test_schain'
    schain_folder = os.path.join(tmp_schains_dir, schain_name)
    os.mkdir(schain_folder)
    toggle_schain_repair_mode(schain_name)
    schain_status_path = os.path.join(schain_folder, 'node_cli.status')
    assert os.path.isfile(schain_status_path)

    assert read_json(schain_status_path) == {
        'repair_ts': CURRENT_TIMESTAMP,
        'schain_name': 'test_schain',
        'snapshot_from': None,
    }

    toggle_schain_repair_mode(schain_name, snapshot_from='127.0.0.1')

    assert read_json(schain_status_path) == {
        'repair_ts': CURRENT_TIMESTAMP,
        'schain_name': 'test_schain',
        'snapshot_from': '127.0.0.1',
    }


@freezegun.freeze_time(CURRENT_DATETIME)
def test_cleanup_sync_datadir(tmp_sync_datadir):
    schain_name = 'test_schain'
    base_folder = Path(tmp_sync_datadir).joinpath(schain_name)
    base_folder.mkdir()
    folders = [
        '28e07f34',
        'block_sigshares_0.db',
        'da_proofs_0.db',
        'filestorage',
        'incoming_msgs_0.db',
        'proposal_hashes_0.db',
        'snapshots',
        'blocks_0.db',
        'da_sigshares_0.db',
        'historic_roots',
        'internal_info_0.db',
        'outgoing_msgs_0.db',
        'proposal_vectors_0.db',
        'block_proposals_0.db',
        'consensus_state_0.db',
        'diffs',
        'historic_state',
        'prices_0.db',
        'randoms_0.db',
    ]
    regular_files = ['HEALTH_CHECK', 'keys.info', 'keys.info.salt']
    snapshots = ['0', '100', '111']
    snapshot_content = ['28e07f34', 'blocks_0.db', 'filestorage', 'prices_0.db']

    for folder_name in folders:
        path = base_folder.joinpath(folder_name)
        path.mkdir()

    for file_name in regular_files:
        path = base_folder.joinpath(file_name)
        path.touch()

    for snapshot_block in snapshots:
        snapshot_folder = base_folder.joinpath('snapshots', snapshot_block)
        snapshot_folder.mkdir()
        for folder in snapshot_content:
            content_path = snapshot_folder.joinpath(folder)
            content_path.mkdir()
            hash_path = snapshot_folder.joinpath('snapshot_hash.txt')
            hash_path.touch()

    with mock.patch('node_cli.core.schains.rm_btrfs_subvolume'):
        cleanup_sync_datadir(schain_name, base_path=tmp_sync_datadir)
        assert not os.path.isdir(base_folder)
