import os
import datetime

import freezegun

from node_cli.core.schains import toggle_schain_repair_mode
from node_cli.utils.helper import read_json


CURRENT_TIMESTAMP = 1594903080
CURRENT_DATETIME = datetime.datetime.utcfromtimestamp(CURRENT_TIMESTAMP)


@freezegun.freeze_time(CURRENT_DATETIME)
def test_toggle_repair_mode(tmp_schains_dir):
    schain_name = "test_schain"
    schain_folder = os.path.join(tmp_schains_dir, schain_name)
    os.mkdir(schain_folder)
    toggle_schain_repair_mode(schain_name)
    schain_status_path = os.path.join(schain_folder, "node_cli.status")
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
