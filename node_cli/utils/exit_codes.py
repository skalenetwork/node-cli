#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
#
#   Copyright (C) 2020 SKALE Labs
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

from enum import IntEnum


class CLIExitCodes(IntEnum):
    """This class contains exit codes for SKALE CLI tools"""
    SUCCESS = 0
    FAILURE = 1
    BAD_API_RESPONSE = 3
    OPERATION_EXECUTION_ERROR = 4
    TRANSACTION_ERROR = 5
    REVERT_ERROR = 6
    BAD_USER_ERROR = 7
    NODE_STATE_ERROR = 8
    UNSAFE_UPDATE = 9
