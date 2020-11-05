import json
import os
from configs import META_FILEPATH
from cli.info import VERSION

DEFAULT_VERSION = '1.0.0'


def get_meta_info() -> dict:
    if not os.path.isfile(META_FILEPATH):
        return {}
    with open(META_FILEPATH) as meta_file:
        meta = json.load(meta_file)
    return meta


def save_meta(meta: dict) -> None:
    with open(META_FILEPATH) as meta_file:
        json.dump(meta, meta_file)


def get_default_meta() -> dict:
    return compose_meta(DEFAULT_VERSION)


def enure_meta(meta: dict = None) -> None:
    if not get_meta_info():
        meta = meta or get_default_meta()
        save_meta(meta)


def compose_meta(version: str) -> dict:
    return {
        'version': version
    }


def update_meta():
    meta = compose_meta(VERSION)
    save_meta(meta)
