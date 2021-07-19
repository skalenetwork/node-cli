#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
#
#   Copyright (C) 2019 SKALE Labs
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

import freezegun

from node_cli.cli.logs import dump
from node_cli.configs import G_CONF_HOME

from tests.helper import run_command
from tests.core.core_logs_test import backup_func, CURRENT_DATETIME, TEST_ARCHIVE_PATH # noqa


@freezegun.freeze_time(CURRENT_DATETIME)
def test_dump(backup_func): # noqa
    result = run_command(dump, [G_CONF_HOME])
    assert result.exit_code == 0
    assert result.output == f'Logs dump created: {TEST_ARCHIVE_PATH}\n'
