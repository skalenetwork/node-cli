import os
from pathlib import Path

import pytest
import mock

from node_cli.core.nginx import (
    generate_nginx_config,
    check_ssl_certs,
    is_skale_node_nginx,
    SSL_KEY_NAME,
    SSL_CRT_NAME,
)
from node_cli.utils.node_type import NodeType, NodeMode
from node_cli.configs import NGINX_TEMPLATE_FILEPATH, NGINX_CONFIG_FILEPATH, NODE_CERTS_PATH

TEST_NGINX_TEMPLATE = """
server {
    listen 3009;
    {% if ssl %}
    listen 311 ssl;
    ssl_certificate     /ssl/ssl_cert;
    ssl_certificate_key /ssl/ssl_key;
    {% endif %}
}

{% if skale_node %}
server {
    listen 80;
    {% if ssl %}
    listen 443 ssl;
    ssl_certificate     /ssl/ssl_cert;
    ssl_certificate_key /ssl/ssl_key;
    {% endif %}
}
{% endif %}
"""

CORE_SSL_SNIPPET = 'listen 311 ssl;'
FILESTORAGE_SNIPPET = 'listen 80;'
FILESTORAGE_SSL_SNIPPET = 'listen 443 ssl;'


@pytest.fixture
def nginx_template():
    """Create a temporary nginx template file."""
    os.makedirs(os.path.dirname(NGINX_TEMPLATE_FILEPATH), exist_ok=True)
    with open(NGINX_TEMPLATE_FILEPATH, 'w') as f:
        f.write(TEST_NGINX_TEMPLATE)
    try:
        yield
    finally:
        if os.path.isfile(NGINX_TEMPLATE_FILEPATH):
            os.remove(NGINX_TEMPLATE_FILEPATH)
        if os.path.isfile(NGINX_CONFIG_FILEPATH):
            os.remove(NGINX_CONFIG_FILEPATH)


@pytest.mark.parametrize(
    'node_type, node_mode, ssl_exists, expected_regular_flag, expected_ssl_flag',
    [
        (NodeType.SKALE, NodeMode.ACTIVE, True, True, True),
        (NodeType.SKALE, NodeMode.ACTIVE, False, True, False),
        (NodeType.SKALE, NodeMode.PASSIVE, True, True, True),
        (NodeType.SKALE, NodeMode.PASSIVE, False, True, False),
        (NodeType.FAIR, NodeMode.ACTIVE, True, False, True),
        (NodeType.FAIR, NodeMode.ACTIVE, False, False, False),
    ],
    ids=[
        'regular_ssl_on',
        'regular_ssl_off',
        'regular_ssl_on',
        'regular_ssl_off',
        'fair_ssl_on',
        'fair_ssl_off',
    ],
)
@mock.patch('node_cli.core.nginx.check_ssl_certs')
@mock.patch('node_cli.core.nginx.TYPE')
def test_generate_nginx_config(
    mock_type,
    mock_check_ssl,
    node_type,
    node_mode,
    ssl_exists,
    expected_regular_flag,
    expected_ssl_flag,
    nginx_template,
):
    mock_type.__eq__.side_effect = lambda other: node_type == other
    mock_type.__ne__.side_effect = lambda other: node_type != other
    mock_check_ssl.return_value = ssl_exists

    generate_nginx_config()

    assert os.path.exists(NGINX_CONFIG_FILEPATH)
    with open(NGINX_CONFIG_FILEPATH) as f:
        rendered_config = f.read()

    rendered_config = rendered_config.strip()

    if expected_regular_flag:
        assert FILESTORAGE_SNIPPET in rendered_config
    else:
        assert FILESTORAGE_SNIPPET not in rendered_config

    if expected_ssl_flag:
        assert CORE_SSL_SNIPPET in rendered_config
    else:
        assert CORE_SSL_SNIPPET not in rendered_config

    if expected_regular_flag and expected_ssl_flag:
        assert FILESTORAGE_SSL_SNIPPET in rendered_config
    else:
        assert FILESTORAGE_SSL_SNIPPET not in rendered_config


def test_check_ssl_certs_exist(ssl_folder):
    Path(os.path.join(NODE_CERTS_PATH, SSL_CRT_NAME)).touch()
    Path(os.path.join(NODE_CERTS_PATH, SSL_KEY_NAME)).touch()
    assert check_ssl_certs()


def test_check_ssl_certs_missing_one(ssl_folder):
    Path(os.path.join(NODE_CERTS_PATH, SSL_CRT_NAME)).touch()
    assert check_ssl_certs() is False


def test_check_ssl_certs_missing_both(ssl_folder):
    assert check_ssl_certs() is False


@pytest.mark.parametrize(
    'node_type, node_mode, expected_result',
    [
        (NodeType.SKALE, NodeMode.ACTIVE, True),
        (NodeType.SKALE, NodeMode.PASSIVE, True),
        (NodeType.FAIR, NodeMode.ACTIVE, False),
    ],
)
@mock.patch('node_cli.core.nginx.TYPE')
def test_is_skale_node_nginx(mock_type, node_type, node_mode, expected_result):
    mock_type.__eq__.side_effect = lambda other: node_type == other
    mock_type.__ne__.side_effect = lambda other: node_type != other

    assert is_skale_node_nginx() is expected_result
