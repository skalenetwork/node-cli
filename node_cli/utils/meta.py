import json
import os
from collections import namedtuple
from node_cli.configs import META_FILEPATH

DEFAULT_VERSION = '1.0.0'
DEFAULT_CONFIG_STREAM = '1.1.0'
DEFAULT_DOCKER_LVMPY_STREAM = '1.0.0'
DEFAULT_OS_ID = 'ubuntu'
DEFAULT_OS_VERSION = '18.04'


class CliMeta(
        namedtuple(
            'Node',
            ['version', 'config_stream', 'docker_lvmpy_stream', 'os_id', 'os_version']
        )
):
    __slots__ = ()

    def __new__(cls, version=DEFAULT_VERSION, config_stream=DEFAULT_CONFIG_STREAM,
                docker_lvmpy_stream=DEFAULT_DOCKER_LVMPY_STREAM, os_id=DEFAULT_OS_ID,
                os_version=DEFAULT_OS_VERSION):
        return super(CliMeta, cls).__new__(
            cls, version, config_stream, docker_lvmpy_stream, os_id, os_version
        )


def get_meta_info(raw: bool = False) -> CliMeta:
    if not os.path.isfile(META_FILEPATH):
        return None
    with open(META_FILEPATH) as meta_file:
        plain_meta = json.load(meta_file)
    if raw:
        return plain_meta
    return CliMeta(**plain_meta)


def save_meta(meta: CliMeta) -> None:
    with open(META_FILEPATH, 'w') as meta_file:
        json.dump(meta._asdict(), meta_file)


def compose_default_meta() -> CliMeta:
    return CliMeta(version=DEFAULT_VERSION,
                   docker_lvmpy_stream=DEFAULT_DOCKER_LVMPY_STREAM,
                   config_stream=DEFAULT_CONFIG_STREAM, os_id=DEFAULT_OS_ID,
                   os_version=DEFAULT_OS_VERSION)


def ensure_meta(meta: CliMeta = None) -> None:
    if not get_meta_info():
        meta = meta or compose_default_meta()
        save_meta(meta)


def update_meta(version: str, config_stream: str,
                docker_lvmpy_stream: str, os_id: str,  os_version: str) -> None:
    ensure_meta()
    meta = CliMeta(version, config_stream, docker_lvmpy_stream, os_id, os_version)
    save_meta(meta)
