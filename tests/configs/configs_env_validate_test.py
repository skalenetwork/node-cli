import os
from typing import Optional
import pytest
import requests
import mock

from node_cli.configs.env import (
    absent_required_params,
    load_env_file,
    build_env_params,
    populate_env_params,
    get_validated_env_config,
    validate_env_params,
    validate_env_type,
    ALLOWED_ENV_TYPES,
    REQUIRED_PARAMS_SKALE,
    REQUIRED_PARAMS_SYNC,
    REQUIRED_PARAMS_MIRAGE_BOOT,
    REQUIRED_PARAMS_MIRAGE,
    OPTIONAL_PARAMS,
)
from node_cli.configs.alias_address_validation import (
    validate_env_alias_or_address,
    validate_contract_address,
    validate_contract_alias,
    get_chain_id,
    get_network_metadata,
    ContractType,
)
from node_cli.utils.exit_codes import CLIExitCodes
from node_cli.utils.node_type import NodeType

ENDPOINT = 'http://localhost:8545'


class FakeResponse:
    def __init__(self, status_code: int, json_data: Optional[dict] = None):
        self.status_code = status_code
        self._json_data = json_data or {}

    def json(self):
        return self._json_data


def test_absent_required_params_returns_missing_keys():
    params = {
        'A': '',
        'B': 'value',
        'C': '',
        'MONITORING_CONTAINERS': 'optional',
    }
    missing = absent_required_params(params)
    assert 'A' in missing
    assert 'C' in missing
    assert 'MONITORING_CONTAINERS' not in missing


def test_load_env_file_nonexistent():
    with pytest.raises(SystemExit) as excinfo:
        load_env_file('nonexistent.env')
    assert excinfo.value.code == CLIExitCodes.FAILURE.value


def test_populate_env_params_updates_from_environ(monkeypatch):
    params = {'FOO': ''}
    monkeypatch.setenv('FOO', 'bar')
    populate_env_params(params)
    assert params['FOO'] == 'bar'


@pytest.mark.parametrize(
    'node_type, is_mirage_boot, expected_keys, unexpected_keys',
    [
        (
            NodeType.REGULAR,
            False,
            REQUIRED_PARAMS_SKALE.keys(),
            {'SCHAIN_NAME'},
        ),
        (
            NodeType.SYNC,
            False,
            REQUIRED_PARAMS_SYNC.keys(),
            set(),
        ),
        (
            NodeType.MIRAGE,
            True,
            REQUIRED_PARAMS_MIRAGE_BOOT.keys(),
            {'DOCKER_LVMPY_STREAM', 'SCHAIN_NAME'},
        ),
        (
            NodeType.MIRAGE,
            False,
            REQUIRED_PARAMS_MIRAGE.keys(),
            {'IMA_CONTRACTS', 'DOCKER_LVMPY_STREAM', 'SCHAIN_NAME'},
        ),
    ],
    ids=['regular', 'sync', 'mirage_boot', 'mirage_regular'],
)
def test_build_env_params_keys(node_type, is_mirage_boot, expected_keys, unexpected_keys):
    params = build_env_params(node_type=node_type, is_mirage_boot=is_mirage_boot)
    param_keys = set(params.keys())

    all_expected = set(expected_keys) | set(OPTIONAL_PARAMS.keys())
    missing_expected = all_expected - param_keys
    assert not missing_expected, f'Missing expected keys: {missing_expected}'

    found_unexpected = set(unexpected_keys) & param_keys
    assert not found_unexpected, f'Found unexpected keys: {found_unexpected}'


@pytest.mark.parametrize(
    'env_types, should_fail',
    [
        (ALLOWED_ENV_TYPES, False),
        (['invalid'], True),
    ],
    ids=[
        'correct_env',
        'invalid_env',
    ],
)
def test_env_types(env_types, should_fail):
    for env_type in env_types:
        if should_fail:
            with pytest.raises(SystemExit):
                validate_env_type(env_type=env_type)
        else:
            validate_env_type(env_type=env_type)


def test_get_chain_id_success(monkeypatch):
    fake_response = FakeResponse(200, {'result': '0x1'})

    def fake_post(url, json):
        return fake_response

    monkeypatch.setattr(requests, 'post', fake_post)
    assert get_chain_id(ENDPOINT) == 1


def test_get_chain_id_failure(monkeypatch):
    fake_response = FakeResponse(404)

    def fake_post(url, json):
        return fake_response

    monkeypatch.setattr(requests, 'post', fake_post)
    with pytest.raises(SystemExit):
        get_chain_id(ENDPOINT)


@pytest.mark.parametrize(
    'metadata,status_code,should_raise',
    [
        ({'networks': [{'chainId': 1, 'path': 'mainnet'}]}, 200, False),
        (None, 404, True),
    ],
)
def test_get_network_metadata(requests_mock, metadata, status_code, should_raise):
    metadata_url = 'https://raw.githubusercontent.com/skalenetwork/skale-contracts/refs/heads/deployments/metadata.json'
    requests_mock.get(metadata_url, json=metadata, status_code=status_code)

    if should_raise:
        with pytest.raises(SystemExit):
            get_network_metadata()
    else:
        assert get_network_metadata() == metadata


@pytest.mark.parametrize(
    'code,should_raise',
    [
        ('0x123', False),
        ('0x', True),
    ],
)
def test_validate_contract_address(requests_mock, code, should_raise):
    requests_mock.post(ENDPOINT, json={'result': code})
    addr = '0x' + 'a' * 40
    if should_raise:
        with pytest.raises(SystemExit):
            validate_contract_address(addr, ENDPOINT)
    else:
        validate_contract_address(addr, ENDPOINT)


@pytest.mark.parametrize(
    'networks,should_raise',
    [
        ([{'chainId': 1, 'path': 'mainnet'}], False),
        ([], True),
    ],
)
def test_validate_contract_alias(requests_mock, networks, should_raise):
    requests_mock.post(ENDPOINT, json={'result': '0x1'})
    metadata_url = 'https://raw.githubusercontent.com/skalenetwork/skale-contracts/refs/heads/deployments/metadata.json'
    requests_mock.get(metadata_url, json={'networks': networks}, status_code=200)

    if not should_raise:
        alias_url = 'https://raw.githubusercontent.com/skalenetwork/skale-contracts/refs/heads/deployments/mainnet/skale-manager/test-alias.json'
        requests_mock.get(alias_url, status_code=200)
        validate_contract_alias('test-alias', ContractType.MANAGER, ENDPOINT)
    else:
        with pytest.raises(SystemExit):
            validate_contract_alias('test-alias', ContractType.MANAGER, ENDPOINT)


def test_validate_env_alias_or_address_with_address(requests_mock):
    addr = '0x' + 'b' * 40
    requests_mock.post(ENDPOINT, json={'result': '0x1'})
    validate_env_alias_or_address(addr, ContractType.IMA, ENDPOINT)


def test_validate_env_alias_or_address_with_alias(requests_mock):
    requests_mock.post(ENDPOINT, json={'result': '0x1'})
    metadata_url = 'https://raw.githubusercontent.com/skalenetwork/skale-contracts/refs/heads/deployments/metadata.json'
    metadata = {'networks': [{'chainId': 1, 'path': 'mainnet'}]}
    requests_mock.get(metadata_url, json=metadata, status_code=200)
    alias_url = 'https://raw.githubusercontent.com/skalenetwork/skale-contracts/refs/heads/deployments/mainnet/mainnet-ima/test-alias.json'
    requests_mock.get(alias_url, status_code=200)
    validate_env_alias_or_address('test-alias', ContractType.IMA, ENDPOINT)


@pytest.mark.parametrize('env_type', ALLOWED_ENV_TYPES)
@pytest.mark.parametrize(
    'required_params, key_to_remove, should_fail',
    [
        (REQUIRED_PARAMS_MIRAGE_BOOT, None, False),
        (REQUIRED_PARAMS_MIRAGE, None, False),
        (REQUIRED_PARAMS_MIRAGE_BOOT, 'IMA_CONTRACTS', True),
        (REQUIRED_PARAMS_MIRAGE_BOOT, 'FILEBEAT_HOST', True),
        (REQUIRED_PARAMS_MIRAGE, 'FILEBEAT_HOST', True),
    ],
    ids=[
        'mirage_boot',
        'mirage_regular',
        'mirage_boot_missing_ima',
        'mirage_boot_missing_filebeat',
        'mirage_regular_missing_filebeat',
    ],
)
@mock.patch('node_cli.configs.env.validate_env_alias_or_address')
@mock.patch('node_cli.configs.env.validate_env_type')
def test_validate_env_params_mirage(
    mock_validate_type,
    mock_validate_alias,
    required_params,
    key_to_remove,
    should_fail,
    env_type,
):
    params = {k: f'{k}_val' for k in required_params}
    params['ENV_TYPE'] = env_type

    if key_to_remove:
        params[key_to_remove] = ''

    if should_fail:
        with pytest.raises(SystemExit):
            validate_env_params(params=params)
    else:
        validate_env_params(params=params)


@pytest.mark.parametrize(
    'node_type, is_boot, required_keys_dict',
    [
        (NodeType.MIRAGE, True, REQUIRED_PARAMS_MIRAGE_BOOT),
        (NodeType.MIRAGE, False, REQUIRED_PARAMS_MIRAGE),
    ],
    ids=['mirage_boot', 'mirage_regular'],
)
@mock.patch('node_cli.configs.alias_address_validation.validate_env_alias_or_address')
@mock.patch('node_cli.configs.alias_address_validation.get_chain_id', return_value=1)
@mock.patch(
    'node_cli.configs.alias_address_validation.get_network_metadata',
    return_value={'networks': [{'chainId': 1, 'path': 'mainnet'}]},
)
def test_get_validated_env_config_mirage_success(
    mock_meta,
    mock_chain,
    mock_validate_alias,
    tmp_path,
    monkeypatch,
    node_type,
    is_boot,
    required_keys_dict,
):
    env_file = tmp_path / 'mirage.env'
    env_content = ''
    expected_config = {}

    for key in {**required_keys_dict, **OPTIONAL_PARAMS}:
        env_value = f'{key}_value'
        if key == 'ENDPOINT':
            env_value = ENDPOINT
        if key == 'ENV_TYPE':
            env_value = 'devnet'
        if key == 'MANAGER_CONTRACTS':
            env_value = '0x' + '1' * 40
        if key == 'IMA_CONTRACTS':
            env_value = '0x' + '2' * 40

        if key in required_keys_dict:
            env_content += f'{key}={env_value}\n'
        monkeypatch.setenv(key, env_value)
        expected_config[key] = env_value

    env_file.write_text(env_content)

    with mock.patch('node_cli.configs.alias_address_validation.requests.post') as mock_post:
        mock_post.return_value = FakeResponse(200, {'result': '0x123'})

        config = get_validated_env_config(
            node_type=node_type, env_filepath=str(env_file), is_mirage_boot=is_boot
        )

    assert config is not None
    assert set(config.keys()) == set(expected_config.keys())
    for key in expected_config:
        assert config[key] == expected_config[key]

    for key in {**required_keys_dict, **OPTIONAL_PARAMS}:
        monkeypatch.delenv(key, raising=False)


def test_get_validated_env_config_missing_file():
    with pytest.raises(SystemExit):
        get_validated_env_config(env_filepath='nonexistent.env', node_type=NodeType.REGULAR)


def test_get_validated_env_config_unreadable_file(tmp_path):
    env_file = tmp_path / 'unreadable.env'
    env_file.touch()
    original_mode = env_file.stat().st_mode
    try:
        os.chmod(env_file, 0o000)
        with pytest.raises(PermissionError):
            get_validated_env_config(env_filepath=str(env_file), node_type=NodeType.REGULAR)
    finally:
        os.chmod(env_file, original_mode)
