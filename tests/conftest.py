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

from mock import Mock
from readsettings import ReadSettings
from configs import CONFIG_FILEPATH


@pytest.fixture
def skip_auth(monkeypatch):
    monkeypatch.setattr('core.helper.cookies_exists', Mock(return_value=True))


@pytest.fixture
def config(monkeypatch):
    cli_config = ReadSettings(CONFIG_FILEPATH)
    cli_config['host'] = 'https://test.com'
    cli_config['cookies'] = b'\x80\x03}q\x00X\n\x00\x00\x00cookie_keyq\x01X\x0c\x00\x00\x00cookie_valueq\x02s.'  # noqa
    cli_config.save()
    yield
    cli_config.clear()
