import json
import os

import pytest

from configs import META_FILEPATH
from tools.meta import (
    CliMeta, compose_default_meta,
    DEFAULT_CONFIG_STREAM, DEFAULT_VERSION,
    ensure_meta, get_meta_info,
    save_meta, update_meta
)


TEST_META = {
    'version': '0.1.1',
    'config_stream': 'develop'
}


@pytest.fixture
def meta_file():
    with open(META_FILEPATH, 'w') as meta_f:
        json.dump(TEST_META, meta_f)
    yield META_FILEPATH
    os.remove(META_FILEPATH)


@pytest.fixture
def ensure_meta_removed():
    yield
    if os.path.isfile(META_FILEPATH):
        os.remove(META_FILEPATH)


def test_get_meta_info(meta_file):
    meta = get_meta_info()
    assert meta == CliMeta(**TEST_META)


def test_get_meta_info_empty():
    meta = get_meta_info()
    assert meta is None


def test_compose_default_meta():
    meta = compose_default_meta()
    assert meta.version == '1.0.0'
    assert meta.config_stream == '1.1.0'


def test_save_meta(meta_file):
    meta = CliMeta(version='1.1.2', config_stream='2.2.2')
    save_meta(meta)
    with open(META_FILEPATH) as meta_f:
        saved_json = json.load(meta_f)
    assert saved_json == {
        'version': '1.1.2',
        'config_stream': '2.2.2'
    }


def test_update_meta(meta_file):
    old_meta = get_meta_info()
    update_meta(version='3.3.3', config_stream='1.1.1')
    meta = get_meta_info()
    meta.version == '3.3.3'
    meta.config_stream == '1.1.1'
    assert meta != old_meta


def test_ensure_meta(ensure_meta_removed):
    ensure_meta()
    assert get_meta_info() == CliMeta(DEFAULT_VERSION, DEFAULT_CONFIG_STREAM)
    ensure_meta(CliMeta(version='1.1.1', config_stream='1.1.1'))
    assert get_meta_info() == CliMeta(DEFAULT_VERSION, DEFAULT_CONFIG_STREAM)
