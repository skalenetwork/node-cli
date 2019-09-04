import os
from pathlib import Path

SKALE_VOLUME_PATH = '/skale_vol'
NODE_DATA_PATH = '/skale_node_data'
HOME_DIR = str(Path.home())

LOCAL_WALLET_FILENAME = 'local_wallet.json'
LOCAL_WALLET_FILEPATH = os.path.join(NODE_DATA_PATH, LOCAL_WALLET_FILENAME)

DEFAULT_NODE_BASE_PORT = 10000