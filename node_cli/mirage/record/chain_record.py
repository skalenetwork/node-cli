#   -*- coding: utf-8 -*-
#
#   This file is part of Node cli
#
#   Copyright (C) 2025 SKALE Labs
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



import logging
from typing import cast
from datetime import datetime

from node_cli.mirage.record.redis_record import FlatRedisRecord, FieldInfo

logger = logging.getLogger(__name__)


CHAIN_RECORD_FIELDS: dict[str, FieldInfo] = {
    'repair_date': FieldInfo('repair_date', datetime, datetime.fromtimestamp(0)),
    'repair_ts': FieldInfo('repair_ts', int, None),
    'snapshot_from': FieldInfo('snapshot_from', str, None),
}


class ChainRecord(FlatRedisRecord):
    def _record_fields(self) -> dict[str, FieldInfo]:
        return CHAIN_RECORD_FIELDS

    @property
    def repair_date(self) -> datetime:
        return cast(datetime, self._get_field('repair_date'))

    @property
    def snapshot_from(self) -> str | None:
        return cast(str | None, self._get_field('snapshot_from'))

    @property
    def repair_ts(self) -> int | None:
        return cast(int | None, self._get_field('repair_ts'))

    def set_repair_date(self, date: datetime) -> None:
        self._set_field('repair_date', date)

    def set_snapshot_from(self, value: str | None) -> None:
        self._set_field('snapshot_from', value)

    def set_repair_ts(self, value: int | None) -> None:
        self._set_field('repair_ts', value)
