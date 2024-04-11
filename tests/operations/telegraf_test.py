import os

import pytest

from node_cli.operations.telegraf import (
    get_telegraf_options,
    generate_telegraf_config,
    TelegrafNotConfiguredError
)


def test_get_telegraf_options():
    env = {
        'INFLUX_TOKEN': 'token',
        'INFLUX_ORG': 'org',
        'INFLUX_BUCKET': 'bucket',
        'INFLUX_URL': 'http://127.0.0.1:8444'
    }
    options = get_telegraf_options(env)
    assert options == {
        'token': 'token',
        'org': 'org',
        'bucket': 'bucket',
        'url': 'http://127.0.0.1:8444'
    }
    env.pop('INFLUX_TOKEN')
    with pytest.raises(TelegrafNotConfiguredError):
        get_telegraf_options(env)


@pytest.fixture
def template_path(tmp_dir_path):
    path = os.path.join(tmp_dir_path, 'telegraf.conf.j2')
    template = """
[[outputs.influxdb_v2]]
bucket = "{{ bucket }}"
organization = "{{ org }}"
token = "{{ token }}"
urls = ["{{ url }}"]

"""
    with open(path, 'w') as tf:
        tf.write(template)
    return path


def test_generate_telegraf_config(tmp_dir_path, template_path):
    test_config_path = os.path.join(tmp_dir_path, 'telegraf.conf')
    generate_telegraf_config({
        'token': 'token',
        'org': 'org',
        'bucket': 'bucket',
        'url': 'http://127.0.0.1:8444'
    }, template_path, test_config_path)

    with open(test_config_path) as config_path:
        config = config_path.read()
        assert config == '\n[[outputs.influxdb_v2]]\nbucket = "bucket"\norganization = "org"\ntoken = "token"\nurls = ["http://127.0.0.1:8444"]\n'  # noqa
