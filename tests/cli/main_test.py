#   -*- coding: utf-8 -*-
#
#   This file is part of skale-node-cli
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


from cli import info
from main import version, attach, host
from tests.helper import run_command


def test_version(config):
    result = run_command(version, [])
    expected = f'SKALE Node CLI version: {info.VERSION}\n'
    assert result.output == expected
    result = run_command(version, ['--short'])
    assert result.output == f'{info.VERSION}\n'


def test_attach():
    result = run_command(attach)
    assert result.exit_code == 2
    expected =  'Usage: attach [OPTIONS] HOST\nTry "attach --help" for help.\n\nError: Missing argument "HOST".\n'  # noqa
    assert result.output == expected

    result = run_command(attach, ['darova'])
    assert result.exit_code == 0
    assert result.output == 'Provided SKALE node host is not valid\n'

    result = run_command(attach, ['http://127.0.0.1', '--skip-check'])
    assert result.output == 'SKALE host: http://127.0.0.1:3007\n'


def test_host():
    result = run_command(host, [])
    assert result.output == 'SKALE node host: http://127.0.0.1:3007\n'
    result = run_command(host, ['--reset'])
    assert result.output == 'Host removed, cookies cleaned.\n'
