import os
from typing import Optional
import pytest
import requests

from node_cli.configs.env import (
    absent_required_params,
    load_env_file,
    build_env_params,
    populate_env_params,
    get_validated_env_config,
    validate_env_params,
    validate_env_type,
    ALLOWED_ENV_TYPES,
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


def test_load_env_file_not_readable(tmp_path):
    # Create a temporary file and remove read permissions
    env_file = tmp_path / 'test.env'
    env_file.write_text('KEY=value')
    os.chmod(env_file, 0o000)
    with pytest.raises(PermissionError):
        load_env_file(str(env_file))
    os.chmod(env_file, 0o644)  # reset permissions


@pytest.mark.parametrize('sync_node,has_schain_name', [(True, True), (False, False)])
def test_build_env_params_sync_and_non_sync(sync_node, has_schain_name):
    params = build_env_params(node_type=NodeType.SYNC if sync_node else NodeType.REGULAR)
    assert ('SCHAIN_NAME' in params) == has_schain_name


def test_populate_env_params_updates_from_environ(monkeypatch):
    params = {'FOO': ''}
    monkeypatch.setenv('FOO', 'bar')
    populate_env_params(params)
    assert params['FOO'] == 'bar'


@pytest.mark.parametrize('env_type', ['mainnet', 'testnet', 'qanet', 'devnet'])
def test_valid_env_types(env_type):
    validate_env_type(env_type)


def test_invalid_env_type():
    with pytest.raises(SystemExit) as excinfo:
        validate_env_type('invalid')
    assert excinfo.value.code == CLIExitCodes.FAILURE.value


def test_get_chain_id_success(monkeypatch):
    fake_response = FakeResponse(200, {'result': '0x1'})

    def fake_post(url, json):
        return fake_response

    monkeypatch.setattr(requests, 'post', fake_post)
    chain_id = get_chain_id('http://localhost:8545')
    assert chain_id == 1


def test_get_chain_id_failure(monkeypatch):
    fake_response = FakeResponse(404)

    def fake_post(url, json):
        return fake_response

    monkeypatch.setattr(requests, 'post', fake_post)
    with pytest.raises(SystemExit) as excinfo:
        get_chain_id('http://localhost:8545')
    assert excinfo.value.code == CLIExitCodes.FAILURE.value


def test_get_network_metadata_success(requests_mock):
    metadata = {'networks': [{'chainId': 1, 'path': 'mainnet'}]}
    metadata_url = (
        'https://raw.githubusercontent.com/skalenetwork/skale-contracts/'
        'refs/heads/deployments/metadata.json'
    )
    requests_mock.get(metadata_url, json=metadata, status_code=200)
    result = get_network_metadata()
    assert result == metadata


def test_get_network_metadata_failure(requests_mock):
    metadata_url = (
        'https://raw.githubusercontent.com/skalenetwork/skale-contracts/'
        'refs/heads/deployments/metadata.json'
    )
    requests_mock.get(metadata_url, status_code=404)
    with pytest.raises(SystemExit) as excinfo:
        get_network_metadata()
    assert excinfo.value.code == CLIExitCodes.FAILURE.value


def test_validate_contract_address_success(requests_mock):
    requests_mock.post(ENDPOINT, json={'result': '0x123'})
    validate_contract_address('0x' + 'a' * 40, ENDPOINT)


def test_validate_contract_address_no_code(requests_mock):
    requests_mock.post(ENDPOINT, json={'result': '0x'})
    with pytest.raises(SystemExit) as excinfo:
        validate_contract_address('0x' + 'a' * 40, ENDPOINT)
    assert excinfo.value.code == CLIExitCodes.FAILURE.value


def test_validate_contract_alias_success(requests_mock):
    requests_mock.post(ENDPOINT, json={'result': '0x1'})
    metadata_url = (
        'https://raw.githubusercontent.com/skalenetwork/skale-contracts/'
        'refs/heads/deployments/metadata.json'
    )
    metadata = {'networks': [{'chainId': 1, 'path': 'mainnet'}]}
    requests_mock.get(metadata_url, json=metadata, status_code=200)
    alias_url = (
        'https://raw.githubusercontent.com/skalenetwork/skale-contracts/'
        'refs/heads/deployments/mainnet/skale-manager/test-alias.json'
    )
    requests_mock.get(alias_url, status_code=200)
    validate_contract_alias('test-alias', ContractType.MANAGER, ENDPOINT)


def test_validate_contract_alias_network_missing(requests_mock):
    requests_mock.post(ENDPOINT, json={'result': '0x1'})
    metadata_url = (
        'https://raw.githubusercontent.com/skalenetwork/skale-contracts/'
        'refs/heads/deployments/metadata.json'
    )
    requests_mock.get(metadata_url, json={'networks': []}, status_code=200)
    with pytest.raises(SystemExit) as excinfo:
        validate_contract_alias('test-alias', ContractType.MANAGER, ENDPOINT)
    assert excinfo.value.code == CLIExitCodes.FAILURE.value


def test_validate_env_alias_or_address_with_address(requests_mock):
    addr = '0x' + 'b' * 40
    requests_mock.post(ENDPOINT, json={'result': '0x1'})
    validate_env_alias_or_address(addr, ContractType.IMA, ENDPOINT)


def test_validate_env_alias_or_address_with_alias(requests_mock):
    requests_mock.post(ENDPOINT, json={'result': '0x1'})
    metadata_url = (
        'https://raw.githubusercontent.com/skalenetwork/skale-contracts/'
        'refs/heads/deployments/metadata.json'
    )
    metadata = {'networks': [{'chainId': 1, 'path': 'mainnet'}]}
    requests_mock.get(metadata_url, json=metadata, status_code=200)
    alias_url = (
        'https://raw.githubusercontent.com/skalenetwork/skale-contracts/'
        'refs/heads/deployments/mainnet/mainnet-ima/test-alias.json'
    )
    requests_mock.get(alias_url, status_code=200)
    validate_env_alias_or_address('test-alias', ContractType.IMA, ENDPOINT)


def test_validate_env_params_missing_key():
    populated_params = {
        'CONTAINER_CONFIGS_STREAM': 'value',
        'ENDPOINT': 'http://localhost:8545',
        'MANAGER_CONTRACTS': '',
        'FILEBEAT_HOST': '127.0.0.1:3010',
        'DISK_MOUNTPOINT': '/dev/sss',
        'SGX_SERVER_URL': 'http://127.0.0.1',
        'DOCKER_LVMPY_STREAM': 'value',
        'ENV_TYPE': 'mainnet',
    }
    with pytest.raises(SystemExit) as excinfo:
        validate_env_params(populated_params)
    assert excinfo.value.code == CLIExitCodes.FAILURE.value


def test_validate_env_params_success(valid_env_params, requests_mock):
    endpoint = valid_env_params['ENDPOINT']
    requests_mock.post(endpoint, json={'result': '0x1'})
    metadata_url = (
        'https://raw.githubusercontent.com/skalenetwork/skale-contracts/'
        'refs/heads/deployments/metadata.json'
    )
    metadata = {'networks': [{'chainId': 1, 'path': 'mainnet'}]}
    requests_mock.get(metadata_url, json=metadata, status_code=200)
    ima_alias_url = (
        'https://raw.githubusercontent.com/skalenetwork/skale-contracts/'
        'refs/heads/deployments/mainnet/mainnet-ima/test-ima.json'
    )
    requests_mock.get(ima_alias_url, status_code=200)
    manager_alias_url = (
        'https://raw.githubusercontent.com/skalenetwork/skale-contracts/'
        'refs/heads/deployments/mainnet/skale-manager/test-manager.json'
    )
    requests_mock.get(manager_alias_url, status_code=200)
    validate_env_params(valid_env_params)


def test_get_validated_env_config_success(
    valid_env_file, mock_chain_response, mock_networks_metadata, requests_mock
):
    requests_mock.post(ENDPOINT, json=mock_chain_response)
    metadata_url = (
        'https://raw.githubusercontent.com/skalenetwork/skale-contracts/'
        'refs/heads/deployments/metadata.json'
    )
    requests_mock.get(metadata_url, json=mock_networks_metadata, status_code=200)
    ima_alias_url = (
        'https://raw.githubusercontent.com/skalenetwork/skale-contracts/'
        'refs/heads/deployments/mainnet/mainnet-ima/test-ima.json'
    )
    requests_mock.get(ima_alias_url, status_code=200)
    manager_alias_url = (
        'https://raw.githubusercontent.com/skalenetwork/skale-contracts/'
        'refs/heads/deployments/mainnet/skale-manager/test-manager.json'
    )
    requests_mock.get(manager_alias_url, status_code=200)
    config = get_validated_env_config(valid_env_file)
    assert config['ENDPOINT'] == 'http://localhost:8545'
    assert config['ENV_TYPE'] in ALLOWED_ENV_TYPES


def test_get_validated_env_config_missing_file():
    with pytest.raises(SystemExit) as excinfo:
        get_validated_env_config('nonexistent.env')
    assert excinfo.value.code == CLIExitCodes.FAILURE.value


def test_get_validated_env_config_unreadable_file(valid_env_file):
    os.chmod(valid_env_file, 0o000)
    with pytest.raises(PermissionError):
        get_validated_env_config(valid_env_file)
    os.chmod(valid_env_file, 0o644)
