import sys
import os
import platform
from pathlib import Path

ENV = os.environ.get('ENV')

home = str(Path.home())

CONFIG_FILENAME = '.skale-cli.yaml'
CONFIG_FILEPATH = os.path.join(home, CONFIG_FILENAME)

CURRENT_FILE_LOCATION = os.path.dirname(os.path.realpath(__file__))


if ENV == 'dev':
    PARDIR = os.path.join(CURRENT_FILE_LOCATION, os.pardir)
else:
    PARDIR = os.path.join(sys._MEIPASS, 'data')


TEXT_FILE = os.path.join(PARDIR, 'text.yml')
DATAFILES_FOLDER = os.path.join(PARDIR, 'datafiles')

THIRD_PARTIES_FOLDER_NAME = 'third_parties'
THIRD_PARTIES_FOLDER_PATH = os.path.join(DATAFILES_FOLDER, THIRD_PARTIES_FOLDER_NAME)

DEPENDENCIES_SCRIPT = os.path.join(DATAFILES_FOLDER, 'dependencies.sh')
INSTALL_SCRIPT = os.path.join(DATAFILES_FOLDER, 'install.sh')
INSTALL_CONVOY_SCRIPT = os.path.join(DATAFILES_FOLDER, 'install_convoy.sh')
UPDATE_NODE_PROJECT_SCRIPT = os.path.join(DATAFILES_FOLDER, 'update_node_project.sh')

URLS = {
    'login': '/login',
    'logout': '/logout',
    'register': '/join',
    'node_info': '/node-info',
    'node_about': '/about-node',
    'create_node': '/create-node',
    'test_host': '/test-host',

    'wallet_info': '/load-wallet',
    'validators_info': '/validators-info',

    'schains_containers': '/containers/schains/list',
    'node_schains': '/schains/list',
    'schain_config': '/schain-config',
    'skale_containers': '/containers/list',

    'logs': '/logs',
    'log_download': '/download-log-file'
}

LONG_LINE = '-' * 50

SKALE_NODE_UI_PORT = 3007
SKALE_NODE_UI_LOCALHOST = 'http://0.0.0.0'
DEFAULT_URL_SCHEME = 'http://'

SKALE_PROJECT_PATH = os.path.join('/skale', 'skale-node')
UNINSTALL_SCRIPT = os.path.join(SKALE_PROJECT_PATH, 'installation', 'uninstall.sh')
UPDATE_SCRIPT = os.path.join(SKALE_PROJECT_PATH, 'installation', 'update.sh')

NODE_DATA_PATH = '/skale_node_data'
TOKENS_FILENAME = 'tokens.json'
TOKENS_FILEPATH = os.path.join(NODE_DATA_PATH, TOKENS_FILENAME)

DEFAULT_MTA_ENDPOINT = 'http://134.209.56.46:1919'
DEFAULT_NODE_GIT_BRANCH = 'alpine'
DEFAULT_RPC_IP = '134.209.56.46'
DEFAULT_RPC_PORT = 1920
DEFAULT_DB_USER = 'root'
DEFAULT_DB_PORT = '3306'

HOST_OS = platform.system()
MAC_OS_SYSTEM_NAME = 'Darwin'