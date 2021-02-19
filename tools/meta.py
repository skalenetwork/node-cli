import json
import os
from collections import namedtuple
from configs import META_FILEPATH

DEFAULT_VERSION = '1.0.0'
DEFAULT_CONFIG_STREAM = '1.1.0'
DEFAULT_DOCKER_LVMPY_STREAM = '1.0.0'

CliMeta = namedtuple(
    'CliMeta',
    ('version', 'config_stream', 'docker_lvmpy_stream'),
    defaults=[
        DEFAULT_VERSION, DEFAULT_CONFIG_STREAM, DEFAULT_DOCKER_LVMPY_STREAM
    ]
)


def get_meta_info() -> CliMeta:
    if not os.path.isfile(META_FILEPATH):
        return None
    with open(META_FILEPATH) as meta_file:
        plain_meta = json.load(meta_file)
    return CliMeta(**plain_meta)


def save_meta(meta: CliMeta) -> None:
    with open(META_FILEPATH, 'w') as meta_file:
        json.dump(meta._asdict(), meta_file)


def compose_default_meta() -> CliMeta:
    return CliMeta(version=DEFAULT_VERSION,
                   docker_lvmpy_stream=DEFAULT_DOCKER_LVMPY_STREAM,
                   config_stream=DEFAULT_CONFIG_STREAM)


def ensure_meta(meta: CliMeta = None) -> None:
    if not get_meta_info():
        meta = meta or compose_default_meta()
        save_meta(meta)


def update_meta(version: str, config_stream: str,
                docker_lvmpy_stream: str) -> None:
    ensure_meta()
    meta = CliMeta(version, config_stream, docker_lvmpy_stream)
    save_meta(meta)
