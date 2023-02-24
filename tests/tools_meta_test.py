import json

from node_cli.configs import META_FILEPATH
from node_cli.utils.meta import (
    CliMeta, compose_default_meta,
    DEFAULT_CONFIG_STREAM, DEFAULT_VERSION,
    ensure_meta, get_meta_info,
    save_meta, update_meta
)
from tests.helper import TEST_META_V1, TEST_META_V2


def test_get_meta_info_v1(meta_file_v1):
    meta = get_meta_info()
    assert meta.version == TEST_META_V1['version']
    assert meta.config_stream == TEST_META_V1['config_stream']
    assert meta.docker_lvmpy_stream == '1.0.0'


def test_get_meta_info_v2(meta_file_v2):
    meta = get_meta_info()
    assert meta.version == TEST_META_V2['version']
    assert meta.config_stream == TEST_META_V2['config_stream']
    assert meta.docker_lvmpy_stream == TEST_META_V2['docker_lvmpy_stream']


def test_get_meta_info_empty():
    meta = get_meta_info()
    assert meta is None


def test_compose_default_meta():
    meta = compose_default_meta()
    assert meta.version == '1.0.0'
    assert meta.config_stream == '1.1.0'
    assert meta.docker_lvmpy_stream == '1.0.0'


def test_save_meta(meta_file_v2):
    meta = CliMeta(version='1.1.2', config_stream='2.2.2')
    save_meta(meta)
    with open(META_FILEPATH) as meta_f:
        saved_json = json.load(meta_f)
    assert saved_json == {
        'version': '1.1.2',
        'config_stream': '2.2.2',
        'docker_lvmpy_stream': '1.0.0'
    }


def test_update_meta(meta_file_v2):
    old_meta = get_meta_info()
    update_meta(version='3.3.3', config_stream='1.1.1',
                docker_lvmpy_stream='1.2.2')
    meta = get_meta_info()
    assert meta.version == '3.3.3'
    assert meta.config_stream == '1.1.1'
    assert meta.docker_lvmpy_stream == '1.2.2'
    assert meta != old_meta


def test_update_meta_from_v1(meta_file_v1):
    update_meta(version='4.4.4', config_stream='beta',
                docker_lvmpy_stream='1.3.3')
    meta = get_meta_info()
    assert meta.version == '4.4.4'
    assert meta.config_stream == 'beta'
    assert meta.docker_lvmpy_stream == '1.3.3'


def test_ensure_meta(ensure_meta_removed):
    ensure_meta()
    assert get_meta_info() == CliMeta(DEFAULT_VERSION, DEFAULT_CONFIG_STREAM)
    ensure_meta(CliMeta(version='1.1.1', config_stream='1.1.1'))
    assert get_meta_info() == CliMeta(DEFAULT_VERSION, DEFAULT_CONFIG_STREAM)
