import os
import shutil
import tarfile
import time
from pathlib import Path

import docker
from docker import errors as docker_errors
import mock
import pytest
import requests

from node_cli.configs import (
    NODE_DATA_PATH,
    SCHAINS_MNT_DIR_REGULAR,
    SCHAINS_MNT_DIR_SINGLE_CHAIN,
)
from node_cli.configs.resource_allocation import RESOURCE_ALLOCATION_FILEPATH

from node_cli.core.node import (
    cleanup,
    compose_node_env,
    get_expected_container_names,
    init,
    is_base_containers_alive,
    is_update_safe,
    pack_dir,
    update,
)
from node_cli.utils.meta import CliMeta
from node_cli.utils.node_type import NodeType, NodeMode
from tests.helper import response_mock, safe_update_api_response, subprocess_run_mock
from tests.resources_test import BIG_DISK_SIZE

dclient = docker.from_env()

ALPINE_IMAGE_NAME = 'alpine:3.12'
CMD = 'sleep 60'

WRONG_CONTAINERS = [
    'WRONG_CONTAINER_1',
    'skale_WRONG_CONTAINER_4',
    'fair_WRONG_CONTAINER_6',
    'passive_WRONG_CONTAINER_8',
]

NODE_TYPE_MODE_BOOT_COMBINATIONS: list[tuple[NodeType, NodeMode, bool]] = [
    (NodeType.SKALE, NodeMode.ACTIVE, False),
    (NodeType.SKALE, NodeMode.PASSIVE, False),
    (NodeType.FAIR, NodeMode.ACTIVE, True),
    (NodeType.FAIR, NodeMode.ACTIVE, False),
]

alive_test_params = [
    pytest.param(
        node_type,
        node_mode,
        is_boot,
        get_expected_container_names(node_type, node_mode, is_boot),
        id=f'{node_type.name}-{node_mode.name}-boot_{is_boot}-correct_containers',
    )
    for node_type, node_mode, is_boot in NODE_TYPE_MODE_BOOT_COMBINATIONS
]

wrong_test_params = [
    pytest.param(
        node_type,
        node_mode,
        is_boot,
        WRONG_CONTAINERS,
        id=f'{node_type.name}-{node_mode.name}-boot_{is_boot}-wrong_containers',
    )
    for node_type, node_mode, is_boot in NODE_TYPE_MODE_BOOT_COMBINATIONS
]

missing_test_params = []
for node_type, node_mode, is_boot in NODE_TYPE_MODE_BOOT_COMBINATIONS:
    expected_names = get_expected_container_names(node_type, node_mode, is_boot)
    containers_to_create = expected_names[1:]
    missing_test_params.append(
        pytest.param(
            node_type,
            node_mode,
            is_boot,
            containers_to_create,
            id=f'{node_type.name}-{node_mode.name}-boot_{is_boot}-missing_containers',
        )
    )


@pytest.fixture
def manage_node_containers(request):
    container_names_to_create = request.param
    created_containers = []
    try:
        for name in container_names_to_create:
            try:
                existing_container = dclient.containers.get(name)
                existing_container.remove(force=True)
            except docker_errors.NotFound:
                pass
            container = dclient.containers.run(
                ALPINE_IMAGE_NAME,
                detach=True,
                name=name,
                command=CMD,
            )
            created_containers.append(container)

        if created_containers:
            time.sleep(2)

        yield created_containers

    finally:
        all_containers_now = dclient.containers.list(all=True)
        cleaned_count = 0
        for container_obj in all_containers_now:
            if container_obj.name in container_names_to_create:
                try:
                    container_obj.remove(force=True)
                    cleaned_count += 1
                except docker_errors.NotFound:
                    pass


@pytest.mark.parametrize(
    'node_type, node_mode, is_boot, manage_node_containers',
    alive_test_params,
    indirect=['manage_node_containers'],
)
def test_is_base_containers_alive(manage_node_containers, node_type, node_mode, is_boot):
    assert (
        is_base_containers_alive(node_type=node_type, node_mode=node_mode, is_fair_boot=is_boot)
        is True
    )


@pytest.mark.parametrize(
    'node_type, node_mode, is_boot, manage_node_containers',
    wrong_test_params,
    indirect=['manage_node_containers'],
)
def test_is_base_containers_alive_wrong(manage_node_containers, node_type, node_mode, is_boot):
    assert (
        is_base_containers_alive(node_type=node_type, node_mode=node_mode, is_fair_boot=is_boot)
        is False
    )


@pytest.mark.parametrize(
    'node_type, node_mode, is_boot, manage_node_containers',
    missing_test_params,
    indirect=['manage_node_containers'],
)
def test_is_base_containers_alive_missing(manage_node_containers, node_type, node_mode, is_boot):
    assert (
        is_base_containers_alive(node_type=node_type, node_mode=node_mode, is_fair_boot=is_boot)
        is False
    )


@pytest.mark.parametrize('node_type, node_mode, is_boot', NODE_TYPE_MODE_BOOT_COMBINATIONS)
def test_is_base_containers_alive_empty(node_type, node_mode, is_boot):
    assert (
        is_base_containers_alive(node_type=node_type, node_mode=node_mode, is_fair_boot=is_boot)
        is False
    )


@pytest.mark.parametrize(
    'node_type, node_mode, expected_mnt_dir',
    [
        (
            NodeType.SKALE,
            NodeMode.ACTIVE,
            SCHAINS_MNT_DIR_REGULAR,
        ),
        (
            NodeType.SKALE,
            NodeMode.PASSIVE,
            SCHAINS_MNT_DIR_SINGLE_CHAIN,
        ),
        (
            NodeType.FAIR,
            NodeMode.ACTIVE,
            SCHAINS_MNT_DIR_SINGLE_CHAIN,
        ),
    ],
    ids=[
        'regular',
        'passive',
        'fair',
    ],
)
def test_compose_node_env(node_type, node_mode, expected_mnt_dir, regular_user_conf):
    result_env = compose_node_env(
        node_type=node_type,
        node_mode=node_mode,
    )

    assert result_env['SCHAINS_MNT_DIR'] == expected_mnt_dir
    assert 'BACKUP_RUN' not in result_env


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


def test_init_node(regular_user_conf, no_resource_file):  # todo: write new init node test
    resp_mock = response_mock(requests.codes.created)
    assert not os.path.isfile(RESOURCE_ALLOCATION_FILEPATH)
    with (
        mock.patch('subprocess.run', new=subprocess_run_mock),
        mock.patch('node_cli.core.resources.get_disk_size', return_value=BIG_DISK_SIZE),
        mock.patch('node_cli.core.host.prepare_host'),
        mock.patch('node_cli.core.host.init_data_dir'),
        mock.patch('node_cli.operations.base.configure_nftables'),
        mock.patch('node_cli.core.node.init_op'),
        mock.patch('node_cli.core.node.is_base_containers_alive', return_value=True),
        mock.patch('node_cli.utils.helper.post_request', resp_mock),
    ):
        init(config_file=regular_user_conf.as_posix(), node_type=NodeType.SKALE)
        assert os.path.isfile(RESOURCE_ALLOCATION_FILEPATH)


def test_update_node(regular_user_conf, mocked_g_config, resource_file, inited_node):
    resp_mock = response_mock(requests.codes.created)
    os.makedirs(NODE_DATA_PATH, exist_ok=True)
    with (
        mock.patch('subprocess.run', new=subprocess_run_mock),
        mock.patch('node_cli.core.node.update_op'),
        mock.patch('node_cli.operations.base.configure_nftables'),
        mock.patch('node_cli.core.host.prepare_host'),
        mock.patch('node_cli.core.node.is_base_containers_alive', return_value=True),
        mock.patch('node_cli.utils.helper.post_request', resp_mock),
        mock.patch('node_cli.core.resources.get_disk_size', return_value=BIG_DISK_SIZE),
        mock.patch('node_cli.core.host.init_data_dir'),
        mock.patch(
            'node_cli.core.node.CliMetaManager.get_meta_info',
            return_value=CliMeta(version='2.6.0', config_stream='3.0.2'),
        ),
    ):
        with mock.patch(
            'node_cli.utils.helper.requests.get', return_value=safe_update_api_response()
        ):  # noqa
            result = update(
                regular_user_conf.as_posix(),
                pull_config_for_schain=None,
                node_type=NodeType.SKALE,
                node_mode=NodeMode.ACTIVE,
            )
            assert result is None


@pytest.mark.parametrize(
    'node_type,node_mode',
    [
        (NodeType.SKALE, NodeMode.ACTIVE),
        (NodeType.SKALE, NodeMode.PASSIVE),
        (NodeType.FAIR, NodeMode.ACTIVE),
    ],
)
@mock.patch('node_cli.core.node.is_admin_running', return_value=False)
@mock.patch('node_cli.core.node.is_api_running', return_value=False)
@mock.patch('node_cli.utils.helper.requests.get')
def test_is_update_safe_when_admin_and_api_not_running(
    mock_requests_get, mock_is_api_running, mock_is_admin_running, node_type, node_mode
):
    assert is_update_safe(node_mode=node_mode) is True
    mock_requests_get.assert_not_called()


@mock.patch('node_cli.core.node.is_admin_running', return_value=False)
@mock.patch('node_cli.core.node.is_api_running', return_value=True)
@mock.patch('node_cli.utils.helper.requests.get')
def test_is_update_safe_when_admin_not_running_for_passive(
    mock_requests_get, mock_is_api_running, mock_is_admin_running
):
    assert is_update_safe(node_mode=NodeMode.PASSIVE) is True
    mock_requests_get.assert_not_called()


@pytest.mark.parametrize(
    'node_type,node_mode',
    [
        (NodeType.SKALE, NodeMode.ACTIVE),
        (NodeType.SKALE, NodeMode.PASSIVE),
        (NodeType.FAIR, NodeMode.ACTIVE),
    ],
)
@pytest.mark.parametrize(
    'api_is_safe, expected_result',
    [(True, True), (False, False)],
    ids=['api_safe', 'api_unsafe'],
)
@mock.patch('node_cli.core.node.is_admin_running', return_value=True)
@mock.patch('node_cli.utils.helper.requests.get')
def test_is_update_safe_when_admin_running(
    mock_requests_get, mock_is_admin_running, api_is_safe, expected_result, node_type, node_mode
):
    mock_requests_get.return_value = safe_update_api_response(safe=api_is_safe)
    assert is_update_safe(node_mode=node_mode) is expected_result
    mock_requests_get.assert_called_once()


@pytest.mark.parametrize('node_type', [NodeType.SKALE, NodeType.FAIR])
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
    assert is_update_safe(node_mode=NodeMode.ACTIVE) is expected_result
    mock_requests_get.assert_called_once()


@pytest.mark.parametrize(
    'node_type,node_mode',
    [
        (NodeType.SKALE, NodeMode.ACTIVE),
        (NodeType.SKALE, NodeMode.PASSIVE),
        (NodeType.FAIR, NodeMode.ACTIVE),
    ],
)
@mock.patch('node_cli.core.node.is_admin_running', return_value=True)
@mock.patch('node_cli.utils.helper.requests.get')
def test_is_update_safe_when_api_call_fails(
    mock_requests_get, mock_is_admin_running, node_type, node_mode
):
    mock_requests_get.side_effect = requests.exceptions.ConnectionError('Test connection error')
    assert is_update_safe(node_mode=node_mode) is False
    mock_requests_get.assert_called_once()


@mock.patch('node_cli.utils.decorators.is_user_valid', return_value=True)
@mock.patch('node_cli.core.node.cleanup_skale_op')
@mock.patch('node_cli.core.node.compose_node_env')
def test_cleanup_success(
    mock_compose_env,
    mock_cleanup_skale_op,
    mock_is_user_valid,
    inited_node,
    resource_alloc,
    meta_file_v3,
    active_node_option,
):
    mock_env = {'ENV_TYPE': 'devnet'}
    mock_compose_env.return_value = mock_env

    cleanup(node_mode=NodeMode.ACTIVE)

    mock_compose_env.assert_called_once_with(NodeType.SKALE, NodeMode.ACTIVE)
    mock_cleanup_skale_op.assert_called_once_with(
        node_mode=NodeMode.ACTIVE, compose_env=mock_env, prune=False
    )
