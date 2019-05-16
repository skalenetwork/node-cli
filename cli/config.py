import os
from pathlib import Path

home = str(Path.home())

CONFIG_FILENAME = '.skale-cli.yaml'
CONFIG_FILEPATH = os.path.join(home, CONFIG_FILENAME)

CURRENT_FILE_LOCATION = os.path.dirname(os.path.realpath(__file__))
PARDIR = os.path.join(CURRENT_FILE_LOCATION, os.pardir)

TEXT_FILE = os.path.join(PARDIR, 'text.yml')

URLS = {
    'login': '/login',
    'node_info': '/node-info'
}

LONG_LINE = '-' * 50
