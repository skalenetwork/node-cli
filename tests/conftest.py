#   -*- coding: utf-8 -*-
#
#   This file is part of SKALE.py
#
#   Copyright (C) 2019 SKALE Labs
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Lesser General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Lesser General Public License for more details.
#
#   You should have received a copy of the GNU Lesser General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.
""" SKALE config test """

import json
import os

import pytest

from readsettings import ReadSettings
from configs import CONFIG_FILEPATH
from configs.resource_allocation import RESOURCE_ALLOCATION_FILEPATH


@pytest.fixture
def config(monkeypatch):
    cli_config = ReadSettings(CONFIG_FILEPATH)
    cli_config['host'] = 'https://test.com'
    cli_config.save()
    yield
    cli_config.clear()


@pytest.fixture
def resource_alloc():
    with open(RESOURCE_ALLOCATION_FILEPATH, 'w') as alloc_file:
        json.dump({}, alloc_file)
    yield RESOURCE_ALLOCATION_FILEPATH
    os.remove(RESOURCE_ALLOCATION_FILEPATH)
