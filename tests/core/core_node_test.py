import os
import shutil
import tarfile
import time
from pathlib import Path

import docker
import mock
import pytest
import requests

from node_cli.configs import NODE_DATA_PATH
from node_cli.configs.resource_allocation import RESOURCE_ALLOCATION_FILEPATH
from node_cli.core.node import (
    get_base_containers_amount,
    is_base_containers_alive,
    init,
    pack_dir,
    update,
    is_update_safe,
)
from node_cli.utils.meta import CliMeta
from node_cli.utils.node_type import NodeType

from tests.helper import response_mock, safe_update_api_response, subprocess_run_mock
from tests.resources_test import BIG_DISK_SIZE

dclient = docker.from_env()

ALPINE_IMAGE_NAME = 'alpine:3.12'
HELLO_WORLD_IMAGE_NAME = 'hello-world'
CMD = 'sleep 10'


@pytest.fixture
def skale_base_containers():
    containers = [
        dclient.containers.run(ALPINE_IMAGE_NAME, detach=True, name=f'skale_test{i}', command=CMD)
        for i in range(get_base_containers_amount())
    ]
    yield containers
    for c in containers:
        c.remove(force=True)


@pytest.fixture
def skale_base_containers_without_one():
    containers = [
        dclient.containers.run(ALPINE_IMAGE_NAME, detach=True, name=f'skale_test{i}', command=CMD)
        for i in range(get_base_containers_amount() - 1)
    ]
    yield containers
    for c in containers:
        c.remove(force=True)


@pytest.fixture
def skale_base_containers_exited():
    containers = [
        dclient.containers.run(HELLO_WORLD_IMAGE_NAME, detach=True, name=f'skale_test{i}')
        for i in range(get_base_containers_amount())
    ]
    time.sleep(10)
    yield containers
    for c in containers:
        c.remove(force=True)


@pytest.fixture
def tmp_dir():
    tmp_dir = 'tmp'
    yield os.path.abspath(tmp_dir)
    shutil.rmtree(tmp_dir)


def test_pack_dir(tmp_dir):
    backup_dir = os.path.join(tmp_dir, 'backup')
    data_dir = os.path.join(backup_dir, 'data')
    trash_dir = os.path.join(backup_dir, 'trash')
    a_data = os.path.join(data_dir, 'a-data')
    b_data = os.path.join(data_dir, 'b-data')
    trash_data = os.path.join(trash_dir, 'trash-data')
    os.makedirs(tmp_dir)
    os.makedirs(data_dir)
    os.makedirs(trash_dir)

    for filepath in (a_data, b_data, trash_data):
        with open(filepath, 'w') as f:
            f.write(f.name)

    archive_path = os.path.abspath(os.path.join(tmp_dir, 'archive.tar.gz'))
    pack_dir(backup_dir, archive_path)
    with tarfile.open(archive_path) as tar:
        print(tar.getnames())
        assert Path(a_data).relative_to(tmp_dir).as_posix() in tar.getnames()
        assert Path(b_data).relative_to(tmp_dir).as_posix() in tar.getnames()
        assert Path(trash_data).relative_to(tmp_dir).as_posix() in tar.getnames()

    cleaned_archive_path = os.path.abspath(os.path.join(tmp_dir, 'cleaned-archive.tar.gz'))
    pack_dir(backup_dir, cleaned_archive_path, exclude=(trash_dir,))
    with tarfile.open(cleaned_archive_path) as tar:
        assert Path(a_data).relative_to(tmp_dir).as_posix() in tar.getnames()
        assert Path(b_data).relative_to(tmp_dir).as_posix() in tar.getnames()
        assert Path(trash_data).relative_to(tmp_dir).as_posix() not in tar.getnames()

    # Not absolute or unrelated path in exclude raises ValueError
    with pytest.raises(ValueError):
        pack_dir(backup_dir, cleaned_archive_path, exclude=('trash_data',))


def test_is_base_containers_alive(skale_base_containers):
    cont = skale_base_containers
    print([c.name for c in cont])
    assert is_base_containers_alive()


def test_is_base_containers_alive_one_failed(skale_base_containers_without_one):
    assert not is_base_containers_alive()


def test_is_base_containers_alive_exited(skale_base_containers_exited):
    assert not is_base_containers_alive()


def test_is_base_containers_alive_empty():
    assert not is_base_containers_alive()


@pytest.fixture
def no_resource_file():
    try:
        yield RESOURCE_ALLOCATION_FILEPATH
    finally:
        if os.path.exists(RESOURCE_ALLOCATION_FILEPATH):
            os.remove(RESOURCE_ALLOCATION_FILEPATH)


@pytest.fixture
def resource_file():
    Path(RESOURCE_ALLOCATION_FILEPATH).touch()
    try:
        yield RESOURCE_ALLOCATION_FILEPATH
    finally:
        if os.path.exists(RESOURCE_ALLOCATION_FILEPATH):
            os.remove(RESOURCE_ALLOCATION_FILEPATH)


def test_init_node(no_resource_file):  # todo: write new init node test
    resp_mock = response_mock(requests.codes.created)
    assert not os.path.isfile(RESOURCE_ALLOCATION_FILEPATH)
    env_filepath = './tests/test-env'
    with (
        mock.patch('subprocess.run', new=subprocess_run_mock),
        mock.patch('node_cli.core.resources.get_disk_size', return_value=BIG_DISK_SIZE),
        mock.patch('node_cli.core.host.prepare_host'),
        mock.patch('node_cli.core.host.init_data_dir'),
        mock.patch('node_cli.operations.base.configure_nftables'),
        mock.patch('node_cli.core.node.init_op'),
        mock.patch('node_cli.core.node.is_base_containers_alive', return_value=True),
        mock.patch('node_cli.utils.helper.post_request', resp_mock),
        mock.patch('node_cli.configs.env.validate_env_params', lambda params: None),
    ):
        init(env_filepath)
        assert os.path.isfile(RESOURCE_ALLOCATION_FILEPATH)


@pytest.mark.parametrize('node_type', [NodeType.REGULAR, NodeType.SYNC, NodeType.MIRAGE])
def test_update_node(node_type, mocked_g_config, resource_file):
    env_filepath = './tests/test-env'
    resp_mock = response_mock(requests.codes.created)
    os.makedirs(NODE_DATA_PATH, exist_ok=True)
    with (
        mock.patch('subprocess.run', new=subprocess_run_mock),
        mock.patch('node_cli.core.node.update_op'),
        mock.patch('node_cli.core.node.get_flask_secret_key'),
        mock.patch('node_cli.core.node.save_env_params'),
        mock.patch('node_cli.operations.base.configure_nftables'),
        mock.patch('node_cli.core.host.prepare_host'),
        mock.patch('node_cli.core.node.is_base_containers_alive', return_value=True),
        mock.patch('node_cli.utils.helper.post_request', resp_mock),
        mock.patch('node_cli.core.resources.get_disk_size', return_value=BIG_DISK_SIZE),
        mock.patch('node_cli.core.host.init_data_dir'),
        mock.patch(
            'node_cli.core.node.get_meta_info',
            return_value=CliMeta(version='2.6.0', config_stream='3.0.2'),
        ),
        mock.patch('node_cli.configs.env.validate_env_params', lambda params: None),
    ):
        with mock.patch(
            'node_cli.utils.helper.requests.get', return_value=safe_update_api_response()
        ):  # noqa
            result = update(env_filepath, pull_config_for_schain=None, node_type=node_type)
            assert result is None


@pytest.mark.parametrize('node_type', [NodeType.REGULAR, NodeType.SYNC, NodeType.MIRAGE])
@mock.patch('node_cli.core.node.is_admin_running', return_value=False)
@mock.patch('node_cli.core.node.is_api_running', return_value=False)
@mock.patch('node_cli.utils.helper.requests.get')
def test_is_update_safe_when_admin_and_api_not_running(
    mock_requests_get, mock_is_api_running, mock_is_admin_running, node_type
):
    assert is_update_safe(node_type=node_type) is True
    mock_requests_get.assert_not_called()


@mock.patch('node_cli.core.node.is_admin_running', return_value=False)
@mock.patch('node_cli.core.node.is_api_running', return_value=True)
@mock.patch('node_cli.utils.helper.requests.get')
def test_is_update_safe_when_admin_not_running_for_sync(
    mock_requests_get, mock_is_api_running, mock_is_admin_running
):
    assert is_update_safe(node_type=NodeType.SYNC) is True
    mock_requests_get.assert_not_called()


@pytest.mark.parametrize('node_type', [NodeType.REGULAR, NodeType.SYNC, NodeType.MIRAGE])
@pytest.mark.parametrize(
    'api_is_safe, expected_result',
    [(True, True), (False, False)],
    ids=['api_safe', 'api_unsafe'],
)
@mock.patch('node_cli.core.node.is_admin_running', return_value=True)
@mock.patch('node_cli.utils.helper.requests.get')
def test_is_update_safe_when_admin_running(
    mock_requests_get, mock_is_admin_running, api_is_safe, expected_result, node_type
):
    mock_requests_get.return_value = safe_update_api_response(safe=api_is_safe)
    assert is_update_safe(node_type=node_type) is expected_result
    mock_requests_get.assert_called_once()


@pytest.mark.parametrize('node_type', [NodeType.REGULAR, NodeType.MIRAGE])
@pytest.mark.parametrize(
    'api_is_safe, expected_result',
    [(True, True), (False, False)],
    ids=['api_safe', 'api_unsafe'],
)
@mock.patch('node_cli.core.node.is_admin_running', return_value=False)
@mock.patch('node_cli.core.node.is_api_running', return_value=True)
@mock.patch('node_cli.utils.helper.requests.get')
def test_is_update_safe_when_only_api_running_for_regular(
    mock_requests_get,
    mock_is_api_running,
    mock_is_admin_running,
    api_is_safe,
    expected_result,
    node_type,
):
    mock_requests_get.return_value = safe_update_api_response(safe=api_is_safe)
    assert is_update_safe(node_type=node_type) is expected_result
    mock_requests_get.assert_called_once()


@pytest.mark.parametrize('node_type', [NodeType.REGULAR, NodeType.SYNC, NodeType.MIRAGE])
@mock.patch('node_cli.core.node.is_admin_running', return_value=True)
@mock.patch('node_cli.utils.helper.requests.get')
def test_is_update_safe_when_api_call_fails(mock_requests_get, mock_is_admin_running, node_type):
    mock_requests_get.side_effect = requests.exceptions.ConnectionError('Test connection error')
    assert is_update_safe(node_type=node_type) is False
    mock_requests_get.assert_called_once()
