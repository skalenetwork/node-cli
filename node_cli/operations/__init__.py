#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
#
#   Copyright (C) 2021 SKALE Labs
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

from node_cli.operations.base import (  # noqa
    update as update_op,
    init as init_op,
    init_sync as init_sync_op,
    init_mirage_boot as init_mirage_boot_op,
    migrate_mirage_boot as migrate_mirage_boot_op,
    update_mirage_boot as update_mirage_boot_op,
    update_sync as update_sync_op,
    turn_off as turn_off_op,
    turn_on as turn_on_op,
    restore as restore_op,
    restore_mirage as restore_mirage_op,
    cleanup_sync as cleanup_sync_op,
    configure_nftables,
)
from node_cli.operations.mirage import (  # noqa
    update_mirage as update_mirage_op,
    MirageUpdateType,
    restore_mirage as restore_mirage_op,
    cleanup as cleanup_mirage_op,
)
