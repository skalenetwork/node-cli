import os
from pathlib import Path

home = str(Path.home())

CONFIG_FILENAME = '.skale-cli.yaml'
CONFIG_FILEPATH = os.path.join(home, CONFIG_FILENAME)

URLS = {
    'login': '/login',
    'node_info': '/node-info'
}

LONG_LINE = '-' * 50
