import os
from typing import Optional
import pytest
import requests

from node_cli.configs.env import (
    absent_params,
    load_env_file,
    build_params,
    populate_params,
    get_env_config,
    validate_params,
    validate_env_type,
    validate_env_alias_or_address,
    validate_contract_address,
    validate_contract_alias,
    get_chain_id,
    get_network_metadata,
    ContractType,
    ALLOWED_ENV_TYPES,
)
from node_cli.utils.exit_codes import CLIExitCodes


# =============================================================================
# Helper fake response for patching requests.get in network helpers
# =============================================================================
class FakeResponse:
    def __init__(self, status_code: int, json_data: Optional[dict] = None):
        self.status_code = status_code
        self._json_data = json_data or {}

    def json(self):
        return self._json_data


# =============================================================================
# Tests for absent_params
# =============================================================================
class TestAbsentParams:
    def test_absent_params_returns_missing_keys(self):
        params = {
            'A': '',  # missing
            'B': 'value',
            'C': '',  # missing
            'MONITORING_CONTAINERS': 'optional',
        }
        missing = absent_params(params)
        # We expect keys A and C to be missing (assuming they are required)
        assert 'A' in missing
        assert 'C' in missing
        # Optional keys should not be flagged
        assert 'MONITORING_CONTAINERS' not in missing


# =============================================================================
# Tests for file loading
# =============================================================================
class TestLoadEnvFile:
    def test_load_env_file_nonexistent(self):
        with pytest.raises(SystemExit) as excinfo:
            load_env_file('nonexistent.env')
        assert excinfo.value.code == CLIExitCodes.FAILURE.value

    def test_load_env_file_not_readable(self, tmp_path):
        # Create a temporary file and remove read permissions
        env_file = tmp_path / 'test.env'
        env_file.write_text('KEY=value')
        os.chmod(env_file, 0o000)
        with pytest.raises(SystemExit) as excinfo:
            load_env_file(str(env_file))
        assert excinfo.value.code == CLIExitCodes.FAILURE.value
        os.chmod(env_file, 0o644)  # reset permissions


# =============================================================================
# Tests for building and populating parameters
# =============================================================================
class TestBuildAndPopulate:
    def test_build_params_sync(self):
        params = build_params(sync_node=True)
        # Should contain SCHAIN_NAME among required keys.
        assert 'SCHAIN_NAME' in params

    def test_build_params_non_sync(self):
        params = build_params(sync_node=False)
        # Should not contain SCHAIN_NAME (only in sync dictionary)
        assert 'SCHAIN_NAME' not in params

    def test_populate_params_updates_from_environ(self, monkeypatch):
        # Start with a base dictionary.
        params = {'FOO': ''}
        monkeypatch.setenv('FOO', 'bar')
        populate_params(params)
        assert params['FOO'] == 'bar'


# =============================================================================
# Tests for validate_env_type
# =============================================================================
class TestEnvType:
    @pytest.mark.parametrize('env_type', ['mainnet', 'testnet', 'qanet', 'devnet'])
    def test_valid_env_types(self, env_type):
        # Should pass without exiting
        validate_env_type(env_type)

    def test_invalid_env_type(self):
        with pytest.raises(SystemExit) as excinfo:
            validate_env_type('invalid')
        assert excinfo.value.code == CLIExitCodes.FAILURE.value


# =============================================================================
# Tests for network helper functions
# =============================================================================
class TestNetworkHelpers:
    def test_get_chain_id_success(self, monkeypatch):
        fake_response = FakeResponse(200, {'result': '0x1'})

        def fake_post(url, json):
            return fake_response

        monkeypatch.setattr(requests, 'post', fake_post)
        chain_id = get_chain_id('http://localhost:8545')
        assert chain_id == 1

    def test_get_chain_id_failure(self, monkeypatch):
        fake_response = FakeResponse(404)

        def fake_post(url, json):
            return fake_response

        monkeypatch.setattr(requests, 'post', fake_post)
        with pytest.raises(SystemExit) as excinfo:
            get_chain_id('http://localhost:8545')
        assert excinfo.value.code == CLIExitCodes.FAILURE.value

    def test_get_network_metadata_success(self, requests_mock):
        metadata = {'networks': [{'chainId': 1, 'path': 'mainnet'}]}
        metadata_url = (
            'https://raw.githubusercontent.com/skalenetwork/skale-contracts/'
            'refs/heads/deployments/metadata.json'
        )
        requests_mock.get(metadata_url, json=metadata, status_code=200)
        result = get_network_metadata()
        assert result == metadata

    def test_get_network_metadata_failure(self, requests_mock):
        metadata_url = (
            'https://raw.githubusercontent.com/skalenetwork/skale-contracts/'
            'refs/heads/deployments/metadata.json'
        )
        requests_mock.get(metadata_url, status_code=404)
        with pytest.raises(SystemExit) as excinfo:
            get_network_metadata()
        assert excinfo.value.code == CLIExitCodes.FAILURE.value


# =============================================================================
# Tests for contract validations
# =============================================================================
class TestContractValidation:
    def test_validate_contract_address_success(self, requests_mock):
        # Simulate a valid contract code response.
        endpoint = 'http://localhost:8545'
        requests_mock.post(endpoint, json={'result': '0x123'})
        # This call should not exit.
        validate_contract_address('0x' + 'a' * 40, endpoint)

    def test_validate_contract_address_no_code(self, requests_mock):
        endpoint = 'http://localhost:8545'
        requests_mock.post(endpoint, json={'result': '0x'})
        with pytest.raises(SystemExit) as excinfo:
            validate_contract_address('0x' + 'a' * 40, endpoint)
        assert excinfo.value.code == CLIExitCodes.FAILURE.value

    def test_validate_contract_alias_success(self, requests_mock):
        endpoint = 'http://localhost:8545'
        # Fake chain ID response.
        requests_mock.post(endpoint, json={'result': '0x1'})
        # Fake metadata response.
        metadata_url = (
            'https://raw.githubusercontent.com/skalenetwork/skale-contracts/'
            'refs/heads/deployments/metadata.json'
        )
        metadata = {'networks': [{'chainId': 1, 'path': 'mainnet'}]}
        requests_mock.get(metadata_url, json=metadata, status_code=200)
        # Fake deployment URL response.
        alias_url = (
            'https://raw.githubusercontent.com/skalenetwork/skale-contracts/'
            'refs/heads/deployments/mainnet/skale-manager/test-alias.json'
        )
        requests_mock.get(alias_url, status_code=200)
        validate_contract_alias('test-alias', ContractType.MANAGER, endpoint)

    def test_validate_contract_alias_network_missing(self, requests_mock):
        endpoint = 'http://localhost:8545'
        requests_mock.post(endpoint, json={'result': '0x1'})
        metadata_url = (
            'https://raw.githubusercontent.com/skalenetwork/skale-contracts/'
            'refs/heads/deployments/metadata.json'
        )
        # Return empty networks list.
        requests_mock.get(metadata_url, json={'networks': []}, status_code=200)
        with pytest.raises(SystemExit) as excinfo:
            validate_contract_alias('test-alias', ContractType.MANAGER, endpoint)
        assert excinfo.value.code == CLIExitCodes.FAILURE.value


# =============================================================================
# Tests for validate_env_alias_or_address and validate_params
# =============================================================================
class TestEnvAliasAndParams:
    def test_validate_env_alias_or_address_with_address(self, requests_mock):
        endpoint = 'http://localhost:8545'
        # Provide a fake contract address: 42 characters starting with '0x'
        addr = '0x' + 'b' * 40
        # Patch validate_contract_address to succeed
        requests_mock.post(endpoint, json={'result': '0x1'})
        validate_env_alias_or_address(addr, ContractType.IMA, endpoint)

    def test_validate_env_alias_or_address_with_alias(self, requests_mock):
        endpoint = 'http://localhost:8545'
        # For alias, we simulate a valid contract alias check.
        # Fake chain ID response:
        requests_mock.post(endpoint, json={'result': '0x1'})
        metadata_url = (
            'https://raw.githubusercontent.com/skalenetwork/skale-contracts/'
            'refs/heads/deployments/metadata.json'
        )
        metadata = {'networks': [{'chainId': 1, 'path': 'mainnet'}]}
        requests_mock.get(metadata_url, json=metadata, status_code=200)
        # Fake deployment response.
        alias_url = (
            'https://raw.githubusercontent.com/skalenetwork/skale-contracts/'
            'refs/heads/deployments/mainnet/mainnet-ima/test-alias.json'
        )
        requests_mock.get(alias_url, status_code=200)
        validate_env_alias_or_address('test-alias', ContractType.IMA, endpoint)

    def test_validate_params_missing_key(self):
        # Create a dictionary missing one required key.
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
            validate_params(populated_params)
        assert excinfo.value.code == CLIExitCodes.FAILURE.value

    def test_validate_params_success(self, valid_env_params, requests_mock):
        endpoint = valid_env_params['ENDPOINT']
        # Fake chain ID response.
        requests_mock.post(endpoint, json={'result': '0x1'})
        # Fake metadata response.
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
        # Should not exit.
        validate_params(valid_env_params)


# =============================================================================
# Tests for get_env_config
# =============================================================================
class TestGetEnvConfig:
    def test_get_env_config_success(
        self, valid_env_file, mock_chain_response, mock_networks_metadata, requests_mock
    ):
        endpoint = 'http://localhost:8545'
        # Patch network calls used in validation
        requests_mock.post(endpoint, json=mock_chain_response)
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
        config = get_env_config(valid_env_file)
        # Assert that keys from the env file are present (using string values)
        assert config['ENDPOINT'] == 'http://localhost:8545'
        # Also check that ENV_TYPE is one of the allowed ones
        assert config['ENV_TYPE'] in ALLOWED_ENV_TYPES

    def test_get_env_config_missing_file(self):
        with pytest.raises(SystemExit) as excinfo:
            get_env_config('nonexistent.env')
        assert excinfo.value.code == CLIExitCodes.FAILURE.value

    def test_get_env_config_unreadable_file(self, valid_env_file):
        os.chmod(valid_env_file, 0o000)
        with pytest.raises(SystemExit) as excinfo:
            get_env_config(valid_env_file)
        assert excinfo.value.code == CLIExitCodes.FAILURE.value
        os.chmod(valid_env_file, 0o644)
