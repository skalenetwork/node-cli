#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
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

import os
import mock
import pytest

TEST_GLOBAL_SKALE_DIR = os.path.join(os.environ.get('HOME_DIR'), 'etc', 'skale')
TEST_G_CONF_FP = os.path.join(TEST_GLOBAL_SKALE_DIR, 'conf.json')


@pytest.fixture()
def mocked_g_config():
    with mock.patch(
        'node_cli.utils.global_config.GLOBAL_SKALE_CONF_FILEPATH',
        new=TEST_G_CONF_FP
    ), mock.patch('node_cli.utils.global_config.GLOBAL_SKALE_DIR', new=TEST_GLOBAL_SKALE_DIR):
        yield
