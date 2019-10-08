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

import pytest
from readsettings import ReadSettings


@pytest.fixture
def config(monkeypatch):
    TEST_PATH = '.skale-cli.yaml'
    config = ReadSettings(TEST_PATH)
    config['host'] = 'https://test.com'
    config['cookies'] = b'\x80\x03}q\x00X\n\x00\x00\x00cookie_keyq\x01X\x0c\x00\x00\x00cookie_valueq\x02s.'  # noqa
