import sys
import os
from pathlib import Path

ENV = os.environ.get('ENV')

home = str(Path.home())

CONFIG_FILENAME = '.skale-cli.yaml'
CONFIG_FILEPATH = os.path.join(home, CONFIG_FILENAME)

CURRENT_FILE_LOCATION = os.path.dirname(os.path.realpath(__file__))
PARDIR = os.path.join(CURRENT_FILE_LOCATION, os.pardir)

if ENV == 'dev':
    TEXT_FILE = os.path.join(PARDIR, 'text.yml')
else:
    BASE_DIR = os.path.join(sys._MEIPASS)
    TEXT_FILE = os.path.join(BASE_DIR, 'texts', 'text.yml')

URLS = {
    'login': '/login',
    'logout': '/logout',
    'node_info': '/node-info',
    'node_about': '/about-node',
    'test_host': '/test-host',

    'wallet_info': '/load-wallet'
}

LONG_LINE = '-' * 50
