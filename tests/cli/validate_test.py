import json
import pathlib
import shutil

import pytest

from node_cli.configs import (CONTRACTS_PATH, G_CONF_HOME,
                              IMA_CONTRACTS_FILEPATH, MANAGER_CONTRACTS_FILEPATH)
from node_cli.cli.validate import abi
from tests.helper import run_command


@pytest.fixture
def contracts_info_dir():
    pathlib.Path(CONTRACTS_PATH).mkdir(parents=True, exist_ok=True)
    yield CONTRACTS_PATH
    shutil.rmtree(CONTRACTS_PATH)


@pytest.fixture
def contract_valid_abi_files(contracts_info_dir):
    json_data = {'test': 'abi'}
    with open(IMA_CONTRACTS_FILEPATH, 'w') as ima_abi_file:
        json.dump(json_data, ima_abi_file)
    with open(MANAGER_CONTRACTS_FILEPATH, 'w') as manager_abi_file:
        json.dump(json_data, manager_abi_file)
    yield IMA_CONTRACTS_FILEPATH, MANAGER_CONTRACTS_FILEPATH


@pytest.fixture
def contract_abi_file_invalid(contracts_info_dir):
    json_data = {'test': 'abi'}
    with open(IMA_CONTRACTS_FILEPATH, 'w') as ima_abi_file:
        json.dump(json_data, ima_abi_file)
    with open(MANAGER_CONTRACTS_FILEPATH, 'w') as manager_abi_file:
        manager_abi_file.write('Invalid json')
    yield IMA_CONTRACTS_FILEPATH, MANAGER_CONTRACTS_FILEPATH


@pytest.fixture
def contract_abi_file_empty(contracts_info_dir):
    json_data = {'test': 'abi'}
    with open(IMA_CONTRACTS_FILEPATH, 'w') as ima_abi_file:
        json.dump(json_data, ima_abi_file)
    yield IMA_CONTRACTS_FILEPATH, MANAGER_CONTRACTS_FILEPATH


def test_validate_abi(contract_valid_abi_files):
    result = run_command(abi)
    assert result.output == 'All abi files are correct json files!\n'
    assert result.exit_code == 0


def test_validate_abi_invalid_file(contract_abi_file_invalid):
    result = run_command(abi)
    assert 'Some files do not exist or are incorrect' in result.output
    assert f'{G_CONF_HOME}.skale/contracts_info/manager.json   error    Failed to load abi file as json' in result.output # noqa
    assert f'{G_CONF_HOME}.skale/contracts_info/ima.json       ok' in result.output
    assert result.exit_code == 0


def test_validate_abi_empty_file(contract_abi_file_empty):
    result = run_command(abi)
    assert 'Some files do not exist or are incorrect' in result.output
    assert f'{G_CONF_HOME}.skale/contracts_info/manager.json   error    No such file' in result.output # noqa
    assert f'{G_CONF_HOME}.skale/contracts_info/ima.json       ok' in result.output
    assert result.exit_code == 0
