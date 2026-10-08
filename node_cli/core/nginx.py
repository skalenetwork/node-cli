#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
#
#   Copyright (C) 2022-Present SKALE Labs
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

import glob
import hashlib
import logging
import os.path
import shutil
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Optional

from filelock import FileLock, Timeout
from jinja2 import Environment

from node_cli.cli.info import TYPE
from node_cli.configs import (
    LEGACY_NGINX_CONFIG_FILEPATH,
    LEGACY_NGINX_TEMPLATE_FILEPATH,
    NGINX_BASE_CONFIG_FILEPATH,
    NGINX_BASE_TEMPLATE_FILEPATH,
    NGINX_CHAINS_PATH,
    NGINX_CONFIG_FILEPATH,
    NGINX_DIR,
    NGINX_LOCK_PATH,
    NGINX_NJS_PATH,
    NGINX_NJS_SOURCE_PATH,
    NGINX_TEMPLATE_DIR,
    NGINX_TEMPLATE_FILEPATH,
    NODE_CERTS_PATH,
)
from node_cli.core.nftables import ServicePort
from node_cli.core.node_options import set_rpc_proxy_override
from node_cli.migrations.nginx_layout import migrate_nginx_layout
from node_cli.utils.decorators import check_inited, check_user
from node_cli.utils.node_type import NodeType
from node_cli.utils.docker_utils import (
    NginxConfigError,
    docker_client,
    nginx_answer,
    reload_nginx_container,
)
from node_cli.utils.helper import check_ssl_certs, process_template, read_file, safe_mkdir

logger = logging.getLogger(__name__)


SSL_KEY_NAME = 'ssl_key'
SSL_CRT_NAME = 'ssl_cert'

# loopback-only location in base.conf that answers with the file's fingerprint
PROBE_PATH = '/.skale-proxy'
BASE_HEADER = '# node base config, rendered by node-cli and skale-admin: fingerprint '
# nginx binds all listeners of a new config or none, so one base.conf server speaks for all
BASE_PROBE_URL = f'http://127.0.0.1:{ServicePort.WATCHDOG_HTTP}{PROBE_PATH}'
# nginx retries a busy listener port five times, 500 ms apart, before it keeps the old config
APPLY_TIMEOUT_SECONDS = 10
POLL_INTERVAL_SECONDS = 0.5
LOCK_TIMEOUT_SECONDS = 120


def generate_nginx_config() -> Optional[str]:
    """Renders the nginx config, returns base.conf or None for streams without it"""
    ssl_on = check_ssl_certs()
    skale_node = is_skale_node_nginx()
    template_data = {
        'ssl': ssl_on,
        'skale_node': skale_node,
    }
    logger.info(f'Processing nginx templates. ssl: {ssl_on}, skale_node: {skale_node}')
    if not os.path.isdir(NGINX_TEMPLATE_DIR):
        # a config stream from before node_data/nginx/ mounts one server file into conf.d
        process_template(
            LEGACY_NGINX_TEMPLATE_FILEPATH, LEGACY_NGINX_CONFIG_FILEPATH, template_data
        )
        return None
    # chains/ is filled by skale-admin, njs/ gets the static handlers from the config repo
    safe_mkdir(NGINX_CHAINS_PATH)
    safe_mkdir(NGINX_NJS_PATH)
    process_template(NGINX_TEMPLATE_FILEPATH, NGINX_CONFIG_FILEPATH, template_data)
    base = render_base_config(ssl_on, skale_node)
    write_atomic(NGINX_BASE_CONFIG_FILEPATH, base)
    for script in glob.glob(os.path.join(NGINX_NJS_SOURCE_PATH, '*.js')):
        shutil.copy(script, NGINX_NJS_PATH)
    migrate_nginx_layout()
    return base


def render_base_config(ssl_on: bool, skale_node: bool) -> str:
    """base.conf fingerprinted with its certificate, rendered identically by skale-admin"""
    template = Environment().from_string(read_file(NGINX_BASE_TEMPLATE_FILEPATH))
    data = {'ssl': ssl_on, 'skale_node': skale_node}
    draft = template.render(data, fingerprint='')
    cert_path = Path(NODE_CERTS_PATH, SSL_CRT_NAME)
    cert = cert_path.read_bytes() if ssl_on and cert_path.is_file() else b''
    fingerprint = hashlib.sha256(draft.encode() + cert).hexdigest()[:16]
    return template.render(data, fingerprint=fingerprint)


def write_atomic(path: str, text: str) -> None:
    """nginx never reads a half-written file: conf.d/*.conf does not match the temporary name"""
    tmp_path = f'{path}.tmp'
    Path(tmp_path).write_text(text)
    os.replace(tmp_path, path)


def base_fingerprint(text: str) -> Optional[str]:
    first_line = text.split('\n', 1)[0]
    return first_line.removeprefix(BASE_HEADER) if first_line.startswith(BASE_HEADER) else None


def wait_for(predicate: Callable[[], bool], timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while not predicate():
        if time.monotonic() >= deadline:
            return False
        time.sleep(POLL_INTERVAL_SECONDS)
    return True


def is_skale_node_nginx() -> bool:
    return TYPE == NodeType.SKALE


@contextmanager
def nginx_lock() -> Iterator[None]:
    """Serialises with skale-admin, which reloads nginx for chain files and certificates"""
    safe_mkdir(NGINX_DIR)
    try:
        with FileLock(NGINX_LOCK_PATH, timeout=LOCK_TIMEOUT_SECONDS):
            yield
    except Timeout as err:
        raise NginxConfigError('skale-admin holds the nginx lock, try again later') from err


def reload_nginx() -> None:
    """Re-render and reload; `nginx -s reload` exits 0 even when nginx keeps its old config"""
    dutils = docker_client()
    base_path = Path(NGINX_BASE_CONFIG_FILEPATH)
    with nginx_lock():
        previous = base_path.read_text() if base_path.is_file() else None
        base = generate_nginx_config()
        try:
            reload_nginx_container(dutils=dutils)
            served = base is None or wait_for(
                lambda: base_served(base, dutils), APPLY_TIMEOUT_SECONDS
            )
            if not served:
                raise NginxConfigError('nginx kept its old configuration, see docker logs sk_nginx')
        except Exception:
            if previous is not None:
                # a file nginx never ran could stop it at its next start
                write_atomic(NGINX_BASE_CONFIG_FILEPATH, previous)
            raise


def base_served(base: str, dutils) -> bool:
    return nginx_answer(BASE_PROBE_URL, dutils=dutils) == f'base {base_fingerprint(base)}'


@check_inited
@check_user
def set_rpc_proxy(mode: str) -> None:
    set_rpc_proxy_override(mode)
    print(
        f'RPC proxy override set to {mode}. skale-admin restarts skaled on the new ports: '
        'SKALE chains at their next check, FAIR at a random time within the next hour.'
    )
