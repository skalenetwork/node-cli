import json
import os

from node_cli.configs import META_FILEPATH
from node_cli.utils.meta import (
    DEFAULT_CONFIG_STREAM,
    DEFAULT_VERSION,
    CliMeta,
    CliMetaManager,
    MirageCliMeta,
    MirageCliMetaManager,
)
from tests.helper import TEST_META_V1, TEST_META_V2, TEST_META_V3


def test_get_meta_info_v1(meta_file_v1):
    meta = CliMetaManager().get_meta_info()
    assert meta.version == TEST_META_V1['version']
    assert meta.config_stream == TEST_META_V1['config_stream']
    assert meta.docker_lvmpy_stream == '1.0.0'


def test_get_meta_info_v2(meta_file_v2):
    meta = CliMetaManager().get_meta_info()
    assert meta.version == TEST_META_V2['version']
    assert meta.config_stream == TEST_META_V2['config_stream']
    assert meta.docker_lvmpy_stream == TEST_META_V2['docker_lvmpy_stream']


def test_get_meta_info_v3(meta_file_v3):
    meta = CliMetaManager().get_meta_info()
    assert meta.version == TEST_META_V3['version']
    assert meta.config_stream == TEST_META_V3['config_stream']
    assert meta.docker_lvmpy_stream == TEST_META_V3['docker_lvmpy_stream']
    assert meta.os_id == TEST_META_V3['os_id']
    assert meta.os_version == TEST_META_V3['os_version']


def test_get_meta_info_empty():
    meta = CliMetaManager().get_meta_info()
    assert meta is None


def test_compose_default_meta():
    meta = CliMetaManager().compose_default_meta()
    assert meta.version == '1.0.0'
    assert meta.config_stream == '1.1.0'
    assert meta.docker_lvmpy_stream == '1.0.0'
    assert meta.os_id == 'ubuntu'
    assert meta.os_version == '18.04'


def test_save_meta(meta_file_v2):
    meta = CliMeta(version='1.1.2', config_stream='2.2.2')
    CliMetaManager().save_meta(meta)
    with open(META_FILEPATH) as meta_f:
        saved_json = json.load(meta_f)
    assert saved_json == {
        'version': '1.1.2',
        'config_stream': '2.2.2',
        'docker_lvmpy_stream': '1.0.0',
        'os_id': 'ubuntu',
        'os_version': '18.04',
    }


def test_update_meta_from_v2_to_v3(meta_file_v2):
    old_meta = CliMetaManager().get_meta_info()
    CliMetaManager().update_meta(
        version='3.3.3',
        config_stream='1.1.1',
        docker_lvmpy_stream='1.2.2',
        os_id='debian',
        os_version='11',
    )
    meta = CliMetaManager().get_meta_info()
    assert meta.version == '3.3.3'
    assert meta.config_stream == '1.1.1'
    assert meta.docker_lvmpy_stream == '1.2.2'
    assert meta.os_id == 'debian'
    assert meta.os_version == '11'
    assert meta != old_meta


def test_update_meta_from_v1(meta_file_v1):
    CliMetaManager().update_meta(
        version='4.4.4',
        config_stream='beta',
        docker_lvmpy_stream='1.3.3',
        os_id='debian',
        os_version='11',
    )
    meta = CliMetaManager().get_meta_info()
    assert meta.version == '4.4.4'
    assert meta.config_stream == 'beta'
    assert meta.docker_lvmpy_stream == '1.3.3'
    assert meta.os_id == 'debian'
    assert meta.os_version == '11'


def test_update_meta_from_v3(meta_file_v3):
    CliMetaManager().update_meta(
        version='5.5.5',
        config_stream='stable',
        docker_lvmpy_stream='1.2.3',
        os_id='ubuntu',
        os_version='20.04',
    )
    meta = CliMetaManager().get_meta_info()
    assert meta.version == '5.5.5'
    assert meta.config_stream == 'stable'
    assert meta.docker_lvmpy_stream == '1.2.3'
    assert meta.os_id == 'ubuntu'
    assert meta.os_version == '20.04'


def test_ensure_meta(ensure_meta_removed):
    CliMetaManager().ensure_meta()
    assert CliMetaManager().get_meta_info() == CliMeta(DEFAULT_VERSION, DEFAULT_CONFIG_STREAM)
    CliMetaManager().ensure_meta(CliMeta(version='1.1.1', config_stream='1.1.1'))
    assert CliMetaManager().get_meta_info() == CliMeta(DEFAULT_VERSION, DEFAULT_CONFIG_STREAM)


def test_mirage_get_meta_info_v1(meta_file_v1):
    meta = MirageCliMetaManager().get_meta_info()
    assert meta.version == TEST_META_V1['version']
    assert meta.config_stream == TEST_META_V1['config_stream']
    assert meta.os_id == 'ubuntu'
    assert meta.os_version == '18.04'


def test_mirage_get_meta_info_v2(meta_file_v2):
    meta = MirageCliMetaManager().get_meta_info()
    assert meta.version == TEST_META_V2['version']
    assert meta.config_stream == TEST_META_V2['config_stream']
    assert meta.os_id == 'ubuntu'  # default value
    assert meta.os_version == '18.04'  # default value


def test_mirage_get_meta_info_v3(meta_file_v3):
    meta = MirageCliMetaManager().get_meta_info()
    assert meta.version == TEST_META_V3['version']
    assert meta.config_stream == TEST_META_V3['config_stream']
    assert meta.os_id == TEST_META_V3['os_id']
    assert meta.os_version == TEST_META_V3['os_version']


def test_mirage_get_meta_info_empty():
    meta = MirageCliMetaManager().get_meta_info()
    assert meta is None


def test_mirage_compose_default_meta():
    meta = MirageCliMetaManager().compose_default_meta()
    assert meta.version == '1.0.0'
    assert meta.config_stream == '1.1.0'
    assert meta.os_id == 'ubuntu'
    assert meta.os_version == '18.04'
    assert not hasattr(meta, 'docker_lvmpy_stream')


def test_mirage_save_meta(meta_file_v2):
    meta = MirageCliMeta(
        version='2.2.2', config_stream='mirage-stable', os_id='debian', os_version='11'
    )
    MirageCliMetaManager().save_meta(meta)
    with open(META_FILEPATH) as meta_f:
        saved_json = json.load(meta_f)
    assert saved_json == {
        'version': '2.2.2',
        'config_stream': 'mirage-stable',
        'os_id': 'debian',
        'os_version': '11',
    }
    assert 'docker_lvmpy_stream' not in saved_json


def test_mirage_update_meta_from_v2_to_v3(meta_file_v2):
    old_meta = MirageCliMetaManager().get_meta_info()
    MirageCliMetaManager().update_meta(
        version='3.3.3',
        config_stream='mirage-beta',
        os_id='debian',
        os_version='11',
    )
    meta = MirageCliMetaManager().get_meta_info()
    assert meta.version == '3.3.3'
    assert meta.config_stream == 'mirage-beta'
    assert meta.os_id == 'debian'
    assert meta.os_version == '11'
    assert meta != old_meta


def test_mirage_update_meta_from_v1(meta_file_v1):
    MirageCliMetaManager().update_meta(
        version='4.4.4',
        config_stream='mirage-develop',
        os_id='centos',
        os_version='8',
    )
    meta = MirageCliMetaManager().get_meta_info()
    assert meta.version == '4.4.4'
    assert meta.config_stream == 'mirage-develop'
    assert meta.os_id == 'centos'
    assert meta.os_version == '8'


def test_mirage_update_meta_from_v3(meta_file_v3):
    MirageCliMetaManager().update_meta(
        version='5.5.5',
        config_stream='mirage-stable',
        os_id='ubuntu',
        os_version='22.04',
    )
    meta = MirageCliMetaManager().get_meta_info()
    assert meta.version == '5.5.5'
    assert meta.config_stream == 'mirage-stable'
    assert meta.os_id == 'ubuntu'
    assert meta.os_version == '22.04'


def test_mirage_ensure_meta(ensure_meta_removed):
    MirageCliMetaManager().ensure_meta()
    assert MirageCliMetaManager().get_meta_info() == MirageCliMeta(
        DEFAULT_VERSION, DEFAULT_CONFIG_STREAM
    )
    MirageCliMetaManager().ensure_meta(MirageCliMeta(version='1.1.1', config_stream='1.1.1'))
    assert MirageCliMetaManager().get_meta_info() == MirageCliMeta(
        DEFAULT_VERSION, DEFAULT_CONFIG_STREAM
    )


def test_mirage_get_meta_info_raw(meta_file_v3):
    raw_meta = MirageCliMetaManager().get_meta_info(raw=True)
    assert isinstance(raw_meta, dict)
    assert raw_meta['version'] == TEST_META_V3['version']
    assert raw_meta['config_stream'] == TEST_META_V3['config_stream']
    assert raw_meta['os_id'] == TEST_META_V3['os_id']
    assert raw_meta['os_version'] == TEST_META_V3['os_version']
    assert 'docker_lvmpy_stream' not in raw_meta


def test_mirage_get_meta_info_raw_empty():
    raw_meta = MirageCliMetaManager().get_meta_info(raw=True)
    assert raw_meta == {}


def test_mirage_asdict():
    meta = MirageCliMeta(
        version='1.2.3', config_stream='test-stream', os_id='fedora', os_version='35'
    )
    meta_dict = meta.asdict()
    expected = {
        'version': '1.2.3',
        'config_stream': 'test-stream',
        'os_id': 'fedora',
        'os_version': '35',
    }
    assert meta_dict == expected
    assert 'docker_lvmpy_stream' not in meta_dict


def test_mirage_meta_compatibility_with_cli_meta_file(meta_file_v3):
    meta = MirageCliMetaManager().get_meta_info()
    assert meta.version == TEST_META_V3['version']
    assert meta.config_stream == TEST_META_V3['config_stream']
    assert meta.os_id == TEST_META_V3['os_id']
    assert meta.os_version == TEST_META_V3['os_version']
    # Should not have docker_lvmpy_stream even though it's in the file
    assert not hasattr(meta, 'docker_lvmpy_stream')


def test_mirage_save_meta_overwrites_cli_meta(meta_file_v3):
    with open(META_FILEPATH) as f:
        original_data = json.load(f)
    assert 'docker_lvmpy_stream' in original_data

    mirage_meta = MirageCliMeta(version='2.0.0', config_stream='mirage-new')
    MirageCliMetaManager().save_meta(mirage_meta)

    with open(META_FILEPATH) as f:
        saved_data = json.load(f)
    assert 'docker_lvmpy_stream' not in saved_data
    assert saved_data['version'] == '2.0.0'
    assert saved_data['config_stream'] == 'mirage-new'


def test_mirage_ensure_meta_with_existing_cli_meta(meta_file_v3):
    MirageCliMetaManager().ensure_meta()
    meta = MirageCliMetaManager().get_meta_info()
    assert meta.version == TEST_META_V3['version']
    assert meta.config_stream == TEST_META_V3['config_stream']


def test_mirage_meta_defaults():
    meta = MirageCliMeta()
    assert meta.version == DEFAULT_VERSION
    assert meta.config_stream == DEFAULT_CONFIG_STREAM
    assert meta.os_id == 'ubuntu'
    assert meta.os_version == '18.04'


def test_mirage_meta_partial_initialization():
    meta = MirageCliMeta(version='1.5.0', os_id='alpine')
    assert meta.version == '1.5.0'
    assert meta.config_stream == DEFAULT_CONFIG_STREAM
    assert meta.os_id == 'alpine'
    assert meta.os_version == '18.04'


def test_mirage_update_meta_ensure_called():
    manager = MirageCliMetaManager()

    manager.update_meta(version='1.0.0', config_stream='test', os_id='ubuntu', os_version='20.04')

    meta = manager.get_meta_info()
    assert meta is not None
    assert meta.version == '1.0.0'
    assert meta.config_stream == 'test'

    if os.path.isfile(META_FILEPATH):
        os.remove(META_FILEPATH)
