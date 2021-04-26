import os
import shlex
import shutil
from datetime import datetime

import pytest
import freezegun

from node_cli.core.logs import create_dump_dir, create_logs_dump
from node_cli.configs import G_CONF_HOME, SKALE_TMP_DIR
from node_cli.utils.docker_utils import docker_client
from node_cli.utils.helper import run_cmd
from node_cli.core.host import safe_mk_dirs


CURRENT_TIMESTAMP = 1594903080
CURRENT_DATETIME = datetime.utcfromtimestamp(CURRENT_TIMESTAMP)
TEST_DUMP_DIR_PATH = os.path.join(SKALE_TMP_DIR, 'skale-logs-dump-2020-07-16--12-38-00')

TEST_IMAGE = 'alpine'
TEST_SKALE_NAME = 'skale_cli_test_container'
TEST_ENTRYPOINT = 'echo Hello, SKALE!'

TEST_ARCHIVE_FOLDER_NAME = 'skale-logs-dump-2020-07-16--12-38-00'
TEST_ARCHIVE_FOLDER_PATH = os.path.join(G_CONF_HOME, f'{TEST_ARCHIVE_FOLDER_NAME}')
TEST_ARCHIVE_PATH = os.path.join(G_CONF_HOME, f'{TEST_ARCHIVE_FOLDER_NAME}.tar.gz')


def _backup_cleanup():
    shutil.rmtree(TEST_DUMP_DIR_PATH, ignore_errors=True)
    shutil.rmtree(TEST_ARCHIVE_FOLDER_PATH, ignore_errors=True)
    if os.path.exists(TEST_ARCHIVE_PATH):
        os.remove(TEST_ARCHIVE_PATH)


@pytest.fixture
def backup_func():
    _backup_cleanup()
    yield
    _backup_cleanup()


@pytest.fixture
def skale_container():
    client = docker_client()
    container = client.containers.run(
        image=TEST_IMAGE,
        name=TEST_SKALE_NAME,
        detach=True,
        entrypoint=TEST_ENTRYPOINT
    )
    yield
    container.remove(force=True)


@freezegun.freeze_time(CURRENT_DATETIME)
def test_create_dump_dir(mocked_g_config, backup_func):
    folder_path, folder_name = create_dump_dir()
    assert folder_path == TEST_DUMP_DIR_PATH
    assert folder_name == 'skale-logs-dump-2020-07-16--12-38-00'


@freezegun.freeze_time(CURRENT_DATETIME)
def test_create_logs_dump(backup_func, skale_container):
    archive_path = create_logs_dump(G_CONF_HOME)
    safe_mk_dirs(TEST_ARCHIVE_FOLDER_PATH)
    cmd = shlex.split(f'tar xf {archive_path} -C {TEST_ARCHIVE_FOLDER_PATH}')
    run_cmd(cmd)

    test_container_log_path = os.path.join(
        TEST_ARCHIVE_FOLDER_PATH, 'containers', f'{TEST_SKALE_NAME}.log'
    )
    with open(test_container_log_path) as data_file:
        content = data_file.read()
    assert content == 'Hello, SKALE!\n'

    assert os.path.exists(os.path.join(TEST_ARCHIVE_FOLDER_PATH, 'removed_containers'))
    assert os.path.exists(os.path.join(TEST_ARCHIVE_FOLDER_PATH, 'cli'))
    assert os.path.exists(os.path.join(TEST_ARCHIVE_FOLDER_PATH, 'containers'))

    assert os.path.isfile(os.path.join(TEST_ARCHIVE_FOLDER_PATH, 'cli', 'debug-node-cli.log'))
    assert os.path.isfile(os.path.join(TEST_ARCHIVE_FOLDER_PATH, 'cli', 'node-cli.log'))


@freezegun.freeze_time(CURRENT_DATETIME)
def test_create_logs_dump_one_container(backup_func, skale_container):
    create_logs_dump(G_CONF_HOME, filter_container='abc')
    test_container_log_path = os.path.join(
        TEST_DUMP_DIR_PATH, 'containers', f'{TEST_SKALE_NAME}.log'
    )
    assert not os.path.isfile(test_container_log_path)
