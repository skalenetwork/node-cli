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

from skale_core.types import EnvType

from node_cli.core.static_config import get_fair_chain_name
from node_cli.fair.record.redis_record import FlatRedisRecord, FieldInfo

logger = logging.getLogger(__name__)


CHAIN_RECORD_FIELDS: dict[str, FieldInfo] = {
    'name': FieldInfo('name', str, ''),
    'config_version': FieldInfo('config_version', str, '0.0.0'),
    'repair_date': FieldInfo('repair_date', datetime, datetime.fromtimestamp(0)),
    'repair_ts': FieldInfo('repair_ts', int, None),
    'snapshot_from': FieldInfo('snapshot_from', str, None),
    'force_skaled_start': FieldInfo('force_skaled_start', bool, False),
}


class ChainRecord(FlatRedisRecord):
    def _record_fields(self) -> dict[str, FieldInfo]:
        return CHAIN_RECORD_FIELDS

    @property
    def config_version(self) -> str:
        return cast(str, self._get_field('config_version'))

    @property
    def repair_date(self) -> datetime:
        return cast(datetime, self._get_field('repair_date'))

    @property
    def snapshot_from(self) -> str | None:
        return cast(str | None, self._get_field('snapshot_from'))

    @property
    def repair_ts(self) -> int | None:
        return cast(int | None, self._get_field('repair_ts'))

    @property
    def force_skaled_start(self) -> bool:
        return cast(bool, self._get_field('force_skaled_start'))

    def set_config_version(self, version: str) -> None:
        self._set_field('config_version', version)

    def set_repair_date(self, date: datetime) -> None:
        self._set_field('repair_date', date)

    def set_snapshot_from(self, value: str | None) -> None:
        self._set_field('snapshot_from', value)

    def set_repair_ts(self, value: int | None) -> None:
        self._set_field('repair_ts', value)

    def set_force_skaled_start(self, value: bool) -> None:
        self._set_field('force_skaled_start', value)


def get_fair_chain_record(env_type: EnvType) -> ChainRecord:
    return ChainRecord(get_fair_chain_name(env_type))


def migrate_chain_record(env_type: EnvType, node_version: str) -> None:
    logger.info('Migrating fair chain record, setting config version to %s', node_version)
    record = get_fair_chain_record(env_type)
    record.set_config_version(node_version)


def update_chain_record(env_type: EnvType, force_skaled_start: bool) -> None:
    record = get_fair_chain_record(env_type)
    record.set_force_skaled_start(force_skaled_start)
    logger.info('Updated fair chain record with force_skaled_start=%s', force_skaled_start)
