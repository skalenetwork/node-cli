#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
#
#   Copyright (C) 2019 SKALE Labs
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

import os
import sys
from node_cli.utils.global_config import read_g_config


GLOBAL_SKALE_DIR = os.getenv('GLOBAL_SKALE_DIR') or '/etc/skale'
GLOBAL_SKALE_CONF_FILENAME = 'conf.json'
GLOBAL_SKALE_CONF_FILEPATH = os.path.join(
    GLOBAL_SKALE_DIR, GLOBAL_SKALE_CONF_FILENAME)
GLOBAL_CONFIG = read_g_config(GLOBAL_SKALE_DIR, GLOBAL_SKALE_CONF_FILEPATH)

G_CONF_USER = GLOBAL_CONFIG['user']
G_CONF_HOME = os.getenv('TEST_HOME_DIR') or GLOBAL_CONFIG['home_dir']

SKALE_STATE_DIR = '/var/lib/skale'
FILESTORAGE_MAPPING = os.path.join(SKALE_STATE_DIR, 'filestorage')
SNAPSHOTS_SHARED_VOLUME = 'shared-space'
SCHAINS_MNT_DIR = '/mnt'

SKALE_DIR = os.path.join(G_CONF_HOME, '.skale')
SKALE_TMP_DIR = os.path.join(SKALE_DIR, '.tmp')

NODE_DATA_PATH = os.path.join(SKALE_DIR, 'node_data')
CONTAINER_CONFIG_PATH = os.path.join(SKALE_DIR, 'config')
CONTAINER_CONFIG_TMP_PATH = os.path.join(SKALE_TMP_DIR, 'config')
CONTRACTS_PATH = os.path.join(SKALE_DIR, 'contracts_info')
REPORTS_PATH = os.path.join(SKALE_DIR, 'reports')
BACKUP_CONTRACTS_PATH = os.path.join(SKALE_DIR, '.old_contracts_info')
INIT_ENV_FILEPATH = os.path.join(SKALE_DIR, '.env')
SKALE_RUN_DIR = '/var/run/skale'

SGX_CERTIFICATES_DIR_NAME = 'sgx_certs'

COMPOSE_PATH = os.path.join(CONTAINER_CONFIG_PATH, 'docker-compose.yml')
SYNC_COMPOSE_PATH = os.path.join(CONTAINER_CONFIG_PATH, 'docker-compose-sync.yml')
ENVIRONMENT_PARAMS_FILEPATH = os.path.join(
    CONTAINER_CONFIG_PATH, 'environment_params.yaml')
NGINX_TEMPLATE_FILEPATH = os.path.join(CONTAINER_CONFIG_PATH, 'nginx.conf.j2')
NGINX_CONFIG_FILEPATH = os.path.join(NODE_DATA_PATH, 'nginx.conf')

LOG_PATH = os.path.join(NODE_DATA_PATH, 'log')
REMOVED_CONTAINERS_FOLDER_NAME = '.removed_containers'
REMOVED_CONTAINERS_FOLDER_PATH = os.path.join(
    LOG_PATH, REMOVED_CONTAINERS_FOLDER_NAME)

ETH_STATE_PATH = os.path.join(NODE_DATA_PATH, 'eth-state')
NODE_CERTS_PATH = os.path.join(NODE_DATA_PATH, 'ssl')

SGX_CERTS_PATH = os.path.join(NODE_DATA_PATH, 'sgx_certs')
SCHAINS_DATA_PATH = os.path.join(NODE_DATA_PATH, 'schains')

CURRENT_FILE_LOCATION = os.path.dirname(os.path.realpath(__file__))
DOTENV_FILEPATH = os.path.join(os.path.dirname(CURRENT_FILE_LOCATION), '.env')

SRC_FILEBEAT_CONFIG_PATH = os.path.join(CONTAINER_CONFIG_PATH, 'filebeat.yml')
FILEBEAT_CONFIG_PATH = os.path.join(NODE_DATA_PATH, 'filebeat.yml')

DOCKER_LVMPY_PATH = os.path.join(SKALE_DIR, 'docker-lvmpy')

IPTABLES_DIR = '/etc/iptables/'
IPTABLES_RULES_STATE_FILEPATH = os.path.join(IPTABLES_DIR, 'rules.v4')

FLASK_SECRET_KEY_FILENAME = 'flask_db_key.txt'
FLASK_SECRET_KEY_FILE = os.path.join(NODE_DATA_PATH, FLASK_SECRET_KEY_FILENAME)

DOCKER_CONFIG_FILEPATH = '/etc/docker/daemon.json'
HIDE_STREAM_LOG = os.getenv('HIDE_STREAM_LOG')


def _get_env():
    try:
        sys._MEIPASS
    except AttributeError:
        return 'dev'
    return 'prod'


ENV = _get_env()
CURRENT_FILE_LOCATION = os.path.dirname(os.path.realpath(__file__))

if ENV == 'dev':
    PARDIR = os.path.join(CURRENT_FILE_LOCATION, os.pardir)
    PROJECT_DIR = os.path.join(PARDIR, os.pardir)
else:
    PARDIR = os.path.join(sys._MEIPASS, 'data')
    PROJECT_DIR = PARDIR

TEXT_FILE = os.path.join(PROJECT_DIR, 'text.yml')
DATAFILES_FOLDER = os.path.join(PARDIR, 'datafiles')

SKALED_SSL_TEST_SCRIPT = os.path.join(DATAFILES_FOLDER, 'skaled-ssl-test')

ALLOCATION_FILEPATH = os.path.join(CONTAINER_CONFIG_PATH,
                                   'schain_allocation.yml')

REDIS_DATA_PATH = os.path.join(NODE_DATA_PATH, 'redis-data')

LONG_LINE = '-' * 50

ADMIN_PORT = 3007
ADMIN_HOST = 'localhost'
DEFAULT_URL_SCHEME = 'http://'

DEFAULT_NODE_BASE_PORT = 10000

BACKUP_ARCHIVE_NAME = 'skale-node-backup'

SSL_FOLDER_PATH = os.path.join(NODE_DATA_PATH, 'ssl')
SSL_CERT_FILEPATH = os.path.join(SSL_FOLDER_PATH, 'ssl_cert')
SSL_KEY_FILEPATH = os.path.join(SSL_FOLDER_PATH, 'ssl_key')


TM_INIT_TIMEOUT = 20
RESTORE_SLEEP_TIMEOUT = 20

MANAGER_CONTRACTS_FILEPATH = os.path.join(CONTRACTS_PATH, 'manager.json')
IMA_CONTRACTS_FILEPATH = os.path.join(CONTRACTS_PATH, 'ima.json')

META_FILEPATH = os.path.join(NODE_DATA_PATH, 'meta.json')

DEFAULT_SSL_CHECK_PORT = 4536

SKALE_NODE_REPO_URL = 'https://github.com/skalenetwork/skale-node.git'
DOCKER_LVMPY_REPO_URL = 'https://github.com/skalenetwork/docker-lvmpy.git'

DOCKER_DEAMON_CONFIG_PATH = '/etc/docker/daemon.json'
DOCKER_DAEMON_HOSTS = ('fd://', 'unix:///var/run/skale/docker.sock')
DOCKER_SERVICE_CONFIG_DIR = '/etc/systemd/system/docker.service.d'
DOCKER_SERVICE_CONFIG_PATH = '/etc/systemd/system/docker.service.d/no-host.conf'
DOCKER_SOCKET_PATH = '/var/run/skale/docker.sock'

CHECK_REPORT_PATH = os.path.join(REPORTS_PATH, 'checks.json')
