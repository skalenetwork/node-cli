#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
#
#   Copyright (C) 2026-Present SKALE Labs
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

import pytest
import tomli_w

from skale.core.settings import get_internal_settings

from node_cli.configs import INTERNAL_SETTINGS_PATH, NODE_SETTINGS_PATH

SKALE_DIR_HOST = './skale-data/'

INTERNAL_SKALE_ACTIVE = {
    'node_type': 'skale',
    'node_mode': 'active',
    'skale_dir_host': SKALE_DIR_HOST,
}

INTERNAL_SKALE_PASSIVE = {
    'node_type': 'skale',
    'node_mode': 'passive',
    'skale_dir_host': SKALE_DIR_HOST,
}

INTERNAL_FAIR_ACTIVE = {
    'node_type': 'fair',
    'node_mode': 'active',
    'skale_dir_host': SKALE_DIR_HOST,
}

INTERNAL_FAIR_PASSIVE = {
    'node_type': 'fair',
    'node_mode': 'passive',
    'skale_dir_host': SKALE_DIR_HOST,
}

_BASE_NODE = {
    'env_type': 'devnet',
    'endpoint': 'http://127.0.0.1:8545',
    'container_stop_timeout': 1,
    'tg_api_key': '123',
    'tg_chat_id': '-1231232',
    'node_version': '0.0.0',
    'block_device': '/dev/sda',
}

NODE_SKALE_ACTIVE = {
    **_BASE_NODE,
    'sgx_url': 'https://localhost:1026',
    'docker_lvmpy_version': '0.0.0',
    'manager_contracts': 'test-manager',
    'ima_contracts': 'test-ima',
}

NODE_SKALE_PASSIVE = {
    **_BASE_NODE,
    'manager_contracts': 'test-manager',
    'ima_contracts': 'test-ima',
    'schain_name': 'test-schain',
    'enforce_btrfs': False,
}

NODE_FAIR_ACTIVE = {
    **_BASE_NODE,
    'sgx_url': 'https://localhost:1026',
    'fair_contracts': 'test-fair',
    'enforce_btrfs': False,
}

NODE_FAIR_PASSIVE = {
    **_BASE_NODE,
    'fair_contracts': 'test-fair',
    'enforce_btrfs': False,
}


def _write_settings(internal: dict, node: dict) -> None:
    INTERNAL_SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    INTERNAL_SETTINGS_PATH.write_bytes(tomli_w.dumps(internal).encode())
    NODE_SETTINGS_PATH.write_bytes(tomli_w.dumps(node).encode())
    get_internal_settings.cache_clear()


def _cleanup_settings() -> None:
    INTERNAL_SETTINGS_PATH.unlink(missing_ok=True)
    NODE_SETTINGS_PATH.unlink(missing_ok=True)
    get_internal_settings.cache_clear()


@pytest.fixture
def skale_active_settings():
    _write_settings(INTERNAL_SKALE_ACTIVE, NODE_SKALE_ACTIVE)
    yield
    _cleanup_settings()


@pytest.fixture
def skale_passive_settings():
    _write_settings(INTERNAL_SKALE_PASSIVE, NODE_SKALE_PASSIVE)
    yield
    _cleanup_settings()


@pytest.fixture
def fair_active_settings():
    _write_settings(INTERNAL_FAIR_ACTIVE, NODE_FAIR_ACTIVE)
    yield
    _cleanup_settings()


@pytest.fixture
def fair_passive_settings():
    _write_settings(INTERNAL_FAIR_PASSIVE, NODE_FAIR_PASSIVE)
    yield
    _cleanup_settings()
