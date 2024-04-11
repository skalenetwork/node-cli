#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
#
#   Copyright (C) 2024-Present SKALE Labs
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

import logging

from node_cli.configs import TELEGRAF_CONFIG_PATH, TELEGRAF_TEMPLATE_PATH
from node_cli.utils.helper import process_template


logger = logging.getLogger(__name__)


class TelegrafNotConfiguredError(Exception):
    pass


def get_telegraf_options(env) -> dict:
    options = {
        'token': env.get('INFLUX_TOKEN'),
        'org': env.get('INFLUX_ORG'),
        'bucket': env.get('INFLUX_BUCKET'),
        'url': env.get('INFLUX_URL')
    }
    missing = list(filter(lambda k: not options[k], options))
    if missing:
        raise TelegrafNotConfiguredError('Missing options {missing}')
    return options


def generate_telegraf_config(
    extra_options: dict,
    template_path: str = TELEGRAF_TEMPLATE_PATH,
    config_path: str = TELEGRAF_CONFIG_PATH
) -> None:
    logger.info('Processing telegraf template')
    process_template(template_path, config_path, extra_options)
