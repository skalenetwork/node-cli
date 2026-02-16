from typing import Optional

import pytest
import requests

from node_cli.configs.alias_address_validation import (
    ContractType,
    get_chain_id,
    get_network_metadata,
    validate_alias_or_address,
    validate_contract_address,
    validate_contract_alias,
)

ENDPOINT = 'http://localhost:8545'


class FakeResponse:
    def __init__(self, status_code: int, json_data: Optional[dict] = None):
        self.status_code = status_code
        self._json_data = json_data or {}

    def json(self):
        return self._json_data


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
    validate_alias_or_address(addr, ContractType.IMA, ENDPOINT)


def test_validate_env_alias_or_address_with_alias(requests_mock):
    requests_mock.post(ENDPOINT, json={'result': '0x1'})
    metadata_url = 'https://raw.githubusercontent.com/skalenetwork/skale-contracts/refs/heads/deployments/metadata.json'
    metadata = {'networks': [{'chainId': 1, 'path': 'mainnet'}]}
    requests_mock.get(metadata_url, json=metadata, status_code=200)
    alias_url = 'https://raw.githubusercontent.com/skalenetwork/skale-contracts/refs/heads/deployments/mainnet/mainnet-ima/test-alias.json'
    requests_mock.get(alias_url, status_code=200)
    validate_alias_or_address('test-alias', ContractType.IMA, ENDPOINT)
