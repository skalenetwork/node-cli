import os
import shutil
import tarfile
import time
from pathlib import Path

import docker
import mock
import pytest
import requests

from node_cli.configs import NODE_DATA_PATH, SCHAINS_MNT_DIR_REGULAR, SCHAINS_MNT_DIR_SINGLE_CHAIN
from node_cli.configs.resource_allocation import RESOURCE_ALLOCATION_FILEPATH
from node_cli.core.node import (
    compose_node_env,
    get_expected_container_names,
    init,
    is_base_containers_alive,
    is_update_safe,
    pack_dir,
    update,
)
from node_cli.utils.meta import CliMeta
from node_cli.utils.node_type import NodeType
from tests.helper import response_mock, safe_update_api_response, subprocess_run_mock
from tests.resources_test import BIG_DISK_SIZE

dclient = docker.from_env()

ALPINE_IMAGE_NAME = 'alpine:3.12'
CMD = 'sleep 60'

WRONG_CONTAINERS = [
    'WRONG_CONTAINER_1',
    'skale_WRONG_CONTAINER_4',
    'mirage_WRONG_CONTAINER_6',
    'sync_WRONG_CONTAINER_8',
]

NODE_TYPE_BOOT_COMBINATIONS: list[tuple[NodeType, bool]] = [
    (NodeType.REGULAR, False),
    (NodeType.SYNC, False),
    (NodeType.MIRAGE, True),
    (NodeType.MIRAGE, False),
]

alive_test_params = [
    pytest.param(
        node_type,
        is_boot,
        get_expected_container_names(node_type, is_boot),
        id=f'{node_type.name}-boot_{is_boot}-correct_containers',
    )
    for node_type, is_boot in NODE_TYPE_BOOT_COMBINATIONS
]

wrong_test_params = [
    pytest.param(
        node_type,
        is_boot,
        WRONG_CONTAINERS,
        id=f'{node_type.name}-boot_{is_boot}-wrong_containers',
    )
    for node_type, is_boot in NODE_TYPE_BOOT_COMBINATIONS
]

missing_test_params = []
for node_type, is_boot in NODE_TYPE_BOOT_COMBINATIONS:
    expected_names = get_expected_container_names(node_type, is_boot)
    containers_to_create = expected_names[1:]
    missing_test_params.append(
        pytest.param(
            node_type,
            is_boot,
            containers_to_create,
            id=f'{node_type.name}-boot_{is_boot}-missing_containers',
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
            except docker.errors.NotFound:
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
                except docker.errors.NotFound:
                    pass


@pytest.mark.parametrize(
    'node_type, is_boot, manage_node_containers',
    alive_test_params,
    indirect=['manage_node_containers'],
)
def test_is_base_containers_alive(manage_node_containers, node_type, is_boot):
    assert is_base_containers_alive(node_type=node_type, is_mirage_boot=is_boot) is True


@pytest.mark.parametrize(
    'node_type, is_boot, manage_node_containers',
    wrong_test_params,
    indirect=['manage_node_containers'],
)
def test_is_base_containers_alive_wrong(manage_node_containers, node_type, is_boot):
    assert is_base_containers_alive(node_type=node_type, is_mirage_boot=is_boot) is False


@pytest.mark.parametrize(
    'node_type, is_boot, manage_node_containers',
    missing_test_params,
    indirect=['manage_node_containers'],
)
def test_is_base_containers_alive_missing(manage_node_containers, node_type, is_boot):
    assert is_base_containers_alive(node_type=node_type, is_mirage_boot=is_boot) is False


@pytest.mark.parametrize('node_type, is_boot', NODE_TYPE_BOOT_COMBINATIONS)
def test_is_base_containers_alive_empty(node_type, is_boot):
    assert is_base_containers_alive(node_type=node_type, is_mirage_boot=is_boot) is False


@pytest.mark.parametrize(
    (
        'node_type, test_user_conf, is_boot, inited_node, sync_schains, expected_mnt_dir,'
        'expect_flask_key, expect_backup_run'
    ),
    [
        (
            NodeType.REGULAR,
            'regular_user_conf',
            False,
            True,
            False,
            SCHAINS_MNT_DIR_REGULAR,
            True,
            False,
        ),
        (
            NodeType.REGULAR,
            'regular_user_conf',
            False,
            True,
            True,
            SCHAINS_MNT_DIR_REGULAR,
            True,
            True,
        ),
        (
            NodeType.SYNC,
            'sync_user_conf',
            False,
            False,
            False,
            SCHAINS_MNT_DIR_SINGLE_CHAIN,
            False,
            False,
        ),
        (
            NodeType.MIRAGE,
            'mirage_boot_user_conf',
            True,
            True,
            False,
            SCHAINS_MNT_DIR_SINGLE_CHAIN,
            True,
            False,
        ),
        (
            NodeType.MIRAGE,
            'mirage_user_conf',
            False,
            True,
            False,
            SCHAINS_MNT_DIR_SINGLE_CHAIN,
            True,
            False,
        ),
    ],
    ids=[
        'regular',
        'regular_sync_flag',
        'sync',
        'mirage_boot',
        'mirage_regular',
    ],
)
def test_compose_node_env(
    request,
    node_type,
    test_user_conf,
    is_boot,
    inited_node,
    sync_schains,
    expected_mnt_dir,
    expect_flask_key,
    expect_backup_run,
):
    user_config_path = request.getfixturevalue(test_user_conf)
    # mock_get_validated.return_value = valid_env_params.copy()
    # if node_type == NodeType.SYNC:
    #     mock_get_validated.return_value['ENV_TYPE'] = 'devnet'
    # else:
    #     mock_get_validated.return_value['ENV_TYPE'] = 'mainnet'
    with (
        mock.patch('node_cli.configs.user.validate_alias_or_address'),
        mock.patch('node_cli.core.node.save_env_params'),
        mock.patch('node_cli.core.node.get_flask_secret_key', return_value='mock_secret'),
    ):
        result_env = compose_node_env(
            env_filepath=user_config_path.as_posix(),
            inited_node=inited_node,
            sync_schains=sync_schains,
            node_type=node_type,
            is_mirage_boot=is_boot,
            save=True,
        )

    # mock_save_params.assert_called_once_with(user_config_path)
    # mock_get_validated.assert_called_once_with(
    #     env_filepath=valid_env_file, node_type=node_type, is_mirage_boot=is_boot
    # )
    assert result_env['SCHAINS_MNT_DIR'] == expected_mnt_dir
    assert (
        'FLASK_SECRET_KEY' in result_env and result_env['FLASK_SECRET_KEY'] is not None
    ) == expect_flask_key
    if expect_flask_key:
        assert result_env['FLASK_SECRET_KEY'] == 'mock_secret'
    should_have_backup = sync_schains and node_type != NodeType.SYNC
    assert ('BACKUP_RUN' in result_env and result_env['BACKUP_RUN'] == 'True') == should_have_backup
    # assert result_env['ENDPOINT'] == valid_env_params['ENDPOINT']


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
        mock.patch('node_cli.configs.user.validate_alias_or_address'),
    ):
        init(env_filepath=regular_user_conf.as_posix(), node_type=NodeType.REGULAR)
        assert os.path.isfile(RESOURCE_ALLOCATION_FILEPATH)


def test_update_node(regular_user_conf, mocked_g_config, resource_file, inited_node):
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
            'node_cli.core.node.CliMetaManager.get_meta_info',
            return_value=CliMeta(version='2.6.0', config_stream='3.0.2'),
        ),
        mock.patch('node_cli.configs.user.validate_alias_or_address'),
    ):
        with mock.patch(
            'node_cli.utils.helper.requests.get', return_value=safe_update_api_response()
        ):  # noqa
            result = update(
                regular_user_conf.as_posix(),
                pull_config_for_schain=None,
                node_type=NodeType.REGULAR,
            )
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
