import os
import shutil
from pathlib import Path

import docker
import pytest
import mock

from node_cli.core.host import is_node_inited
from node_cli.core.nftables import NFTablesError
from filelock import FileLock

from node_cli.core.nginx import (
    BASE_PROBE_URL,
    base_fingerprint,
    generate_nginx_config,
    check_ssl_certs,
    is_skale_node_nginx,
    reload_nginx,
    render_base_config,
    SSL_KEY_NAME,
    SSL_CRT_NAME,
)
from node_cli.core.ssl.upload import upload_cert
from node_cli.core.node_options import (
    NodeOptions,
    hold_rpc_proxy_for_boot,
    release_rpc_proxy_boot_hold,
    set_rpc_proxy_override,
)
from node_cli.migrations.nginx_layout import LEGACY_NGINX_BACKUP_FILEPATH
from node_cli.utils.docker_utils import NginxConfigError, nginx_answer, reload_nginx_container
from node_cli.utils.node_type import NodeType, NodeMode
from node_cli.configs import (
    LEGACY_NGINX_CONFIG_FILEPATH,
    NGINX_BASE_CONFIG_FILEPATH,
    NGINX_BASE_TEMPLATE_FILEPATH,
    NGINX_CHAINS_PATH,
    NGINX_CONFIG_FILEPATH,
    NGINX_DIR,
    NGINX_LOCK_PATH,
    NGINX_NJS_PATH,
    NGINX_NJS_SOURCE_PATH,
    NGINX_TEMPLATE_FILEPATH,
    NODE_CERTS_PATH,
)

TEST_NGINX_MAIN_TEMPLATE = """
events {}
http {
    include /etc/nginx/conf.d/*.conf;
}
"""

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
    """Create temporary main and base nginx templates and an njs handler."""
    os.makedirs(os.path.dirname(NGINX_TEMPLATE_FILEPATH), exist_ok=True)
    os.makedirs(NGINX_NJS_SOURCE_PATH, exist_ok=True)
    with open(NGINX_TEMPLATE_FILEPATH, 'w') as f:
        f.write(TEST_NGINX_MAIN_TEMPLATE)
    with open(NGINX_BASE_TEMPLATE_FILEPATH, 'w') as f:
        f.write(TEST_NGINX_TEMPLATE)
    with open(os.path.join(NGINX_NJS_SOURCE_PATH, 'rpc.js'), 'w') as f:
        f.write('export default {};\n')
    try:
        yield
    finally:
        for path in (NGINX_TEMPLATE_FILEPATH, NGINX_BASE_TEMPLATE_FILEPATH):
            if os.path.isfile(path):
                os.remove(path)
        shutil.rmtree(NGINX_NJS_SOURCE_PATH, ignore_errors=True)
        shutil.rmtree(NGINX_DIR, ignore_errors=True)
        for path in (LEGACY_NGINX_CONFIG_FILEPATH, LEGACY_NGINX_BACKUP_FILEPATH):
            if os.path.isfile(path):
                os.remove(path)


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
    assert os.path.exists(NGINX_BASE_CONFIG_FILEPATH)
    with open(NGINX_BASE_CONFIG_FILEPATH) as f:
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


@mock.patch('node_cli.core.nginx.check_ssl_certs', return_value=False)
def test_generate_nginx_config_layout(mock_check_ssl, nginx_template):
    generate_nginx_config()
    assert os.path.isdir(NGINX_CHAINS_PATH)
    assert os.path.isfile(os.path.join(NGINX_NJS_PATH, 'rpc.js'))
    with open(NGINX_CONFIG_FILEPATH) as f:
        assert 'include /etc/nginx/conf.d/*.conf;' in f.read()


@mock.patch('node_cli.core.nginx.check_ssl_certs', return_value=False)
def test_generate_nginx_config_migrates_legacy_file(mock_check_ssl, nginx_template):
    Path(LEGACY_NGINX_CONFIG_FILEPATH).write_text('server {}')
    assert is_node_inited()
    generate_nginx_config()
    assert not os.path.exists(LEGACY_NGINX_CONFIG_FILEPATH)
    with open(LEGACY_NGINX_BACKUP_FILEPATH) as f:
        assert f.read() == 'server {}'
    assert is_node_inited()


@mock.patch('node_cli.core.nginx.check_ssl_certs', return_value=False)
def test_generate_nginx_config_legacy_stream(mock_check_ssl, nginx_template):
    # streams released before the directory layout have no base.conf.j2
    os.remove(NGINX_BASE_TEMPLATE_FILEPATH)
    generate_nginx_config()
    assert os.path.isfile(LEGACY_NGINX_CONFIG_FILEPATH)
    assert not os.path.exists(NGINX_CONFIG_FILEPATH)
    assert is_node_inited()


def test_is_node_inited_marker(nginx_template):
    assert not is_node_inited()
    Path(LEGACY_NGINX_CONFIG_FILEPATH).write_text('server {}')
    assert is_node_inited()
    os.remove(LEGACY_NGINX_CONFIG_FILEPATH)
    os.makedirs(NGINX_DIR, exist_ok=True)
    Path(NGINX_CONFIG_FILEPATH).touch()
    assert is_node_inited()


def nginx_container_mock(status='running', test_code=0, reload_code=0):
    container = mock.Mock(status=status)
    results = {
        ('nginx', '-t'): mock.Mock(exit_code=test_code, output=b'test output'),
        ('nginx', '-s', 'reload'): mock.Mock(exit_code=reload_code, output=b'no master'),
    }
    container.exec_run.side_effect = lambda cmd: results[tuple(cmd)]
    dclient = mock.Mock()
    dclient.containers.get.return_value = container
    return dclient, container


def test_reload_nginx_container():
    dclient, container = nginx_container_mock()
    reload_nginx_container(dutils=dclient)
    assert [c.args[0] for c in container.exec_run.call_args_list] == [
        ['nginx', '-t'],
        ['nginx', '-s', 'reload'],
    ]
    container.restart.assert_not_called()


def test_reload_nginx_container_bad_config():
    dclient, container = nginx_container_mock(test_code=1)
    with pytest.raises(NginxConfigError):
        reload_nginx_container(dutils=dclient)
    # nginx keeps serving the old config
    assert container.exec_run.call_count == 1
    container.restart.assert_not_called()


def test_reload_nginx_container_reload_fails():
    dclient, container = nginx_container_mock(reload_code=1)
    with pytest.raises(NginxConfigError, match='no master'):
        reload_nginx_container(dutils=dclient)


def test_reload_nginx_container_not_running():
    dclient, container = nginx_container_mock(status='exited')
    reload_nginx_container(dutils=dclient)
    container.restart.assert_called_once()
    container.exec_run.assert_not_called()


def test_nginx_answer():
    dclient, container = nginx_container_mock()
    container.exec_run.side_effect = None
    container.exec_run.return_value = mock.Mock(exit_code=0, output=b'base 0123\n')
    assert nginx_answer('http://127.0.0.1:3009/.skale-proxy', dutils=dclient) == 'base 0123'
    container.exec_run.return_value = mock.Mock(exit_code=7, output=b'')
    assert nginx_answer('https://127.0.0.1:311/.skale-proxy', dutils=dclient) is None
    dclient.containers.get.side_effect = docker.errors.NotFound('sk_nginx')
    assert nginx_answer('http://127.0.0.1:3009/.skale-proxy', dutils=dclient) is None


def test_rpc_proxy_override(active_node_option):
    node_options = NodeOptions()
    assert node_options.rpc_proxy is None
    set_rpc_proxy_override('on')
    assert NodeOptions().rpc_proxy is True
    set_rpc_proxy_override('off')
    assert NodeOptions().rpc_proxy is False
    set_rpc_proxy_override('default')
    assert NodeOptions().rpc_proxy is None


def test_rpc_proxy_boot_hold(active_node_option):
    hold_rpc_proxy_for_boot()
    assert NodeOptions().rpc_proxy is False
    assert NodeOptions().rpc_proxy_boot_hold
    release_rpc_proxy_boot_hold()
    assert NodeOptions().rpc_proxy is None
    assert not NodeOptions().rpc_proxy_boot_hold

    # an operator choice survives the boot phase
    set_rpc_proxy_override('on')
    hold_rpc_proxy_for_boot()
    assert NodeOptions().rpc_proxy is True
    release_rpc_proxy_boot_hold()
    assert NodeOptions().rpc_proxy is True


FINGERPRINT_TEMPLATE = """# node base config, rendered by node-cli and skale-admin: fingerprint {{ fingerprint }}
server {
    listen 3009;
    {% if ssl %}listen 311 ssl;{% endif %}
    location = /.skale-proxy { return 200 'base {{ fingerprint }}'; }
}
"""


@pytest.fixture
def fingerprint_template(nginx_template):
    with open(NGINX_BASE_TEMPLATE_FILEPATH, 'w') as f:
        f.write(FINGERPRINT_TEMPLATE)


def test_render_base_config_fingerprint(fingerprint_template, ssl_folder):
    plain = render_base_config(ssl_on=False, skale_node=True)
    assert render_base_config(ssl_on=False, skale_node=True) == plain
    fingerprint = base_fingerprint(plain)
    assert len(fingerprint) == 16
    assert f"return 200 'base {fingerprint}';" in plain

    cert_path = Path(NODE_CERTS_PATH, SSL_CRT_NAME)
    cert_path.write_text('first certificate')
    with_ssl = render_base_config(ssl_on=True, skale_node=True)
    assert base_fingerprint(with_ssl) != fingerprint
    # a rotated certificate changes the file even though the listeners stay the same
    cert_path.write_text('second certificate')
    rotated = render_base_config(ssl_on=True, skale_node=True)
    assert base_fingerprint(rotated) != base_fingerprint(with_ssl)
    assert rotated.replace(base_fingerprint(rotated), '') == with_ssl.replace(
        base_fingerprint(with_ssl), ''
    )


def read_base() -> str:
    with open(NGINX_BASE_CONFIG_FILEPATH) as f:
        return f.read()


def serve_base_on_disk(url, dutils=None):
    return f'base {base_fingerprint(read_base())}'


@mock.patch('node_cli.core.nginx.POLL_INTERVAL_SECONDS', 0)
@mock.patch('node_cli.core.nginx.check_ssl_certs', return_value=False)
@mock.patch('node_cli.core.nginx.docker_client')
@mock.patch('node_cli.core.nginx.reload_nginx_container')
def test_reload_nginx_waits_for_nginx_to_serve_new_base(
    mock_reload, mock_client, mock_ssl, fingerprint_template
):
    stale = ['base 0000000000000000']

    def nginx_catches_up(url, dutils=None):
        return stale.pop() if stale else serve_base_on_disk(url)

    with mock.patch('node_cli.core.nginx.nginx_answer', side_effect=nginx_catches_up) as answer:
        reload_nginx()
    mock_reload.assert_called_once()
    assert [call.args[0] for call in answer.call_args_list] == [BASE_PROBE_URL] * 2


@mock.patch('node_cli.core.nginx.check_ssl_certs', return_value=False)
@mock.patch('node_cli.core.nginx.docker_client')
@mock.patch('node_cli.core.nginx.reload_nginx_container')
def test_reload_nginx_legacy_stream(mock_reload, mock_client, mock_ssl, nginx_template):
    os.remove(NGINX_BASE_TEMPLATE_FILEPATH)
    with mock.patch('node_cli.core.nginx.nginx_answer') as answer:
        reload_nginx()
    mock_reload.assert_called_once()
    answer.assert_not_called()


@mock.patch('node_cli.core.nginx.APPLY_TIMEOUT_SECONDS', 0.2)
@mock.patch('node_cli.core.nginx.POLL_INTERVAL_SECONDS', 0.05)
@mock.patch('node_cli.core.nginx.check_ssl_certs', return_value=False)
@mock.patch('node_cli.core.nginx.docker_client')
@mock.patch('node_cli.core.nginx.reload_nginx_container')
def test_reload_nginx_restores_base_nginx_did_not_take(
    mock_reload, mock_client, mock_ssl, fingerprint_template
):
    os.makedirs(os.path.dirname(NGINX_BASE_CONFIG_FILEPATH), exist_ok=True)
    with open(NGINX_BASE_CONFIG_FILEPATH, 'w') as f:
        f.write('# the base.conf nginx still runs\n')
    # the reload signal was sent, but nginx still answers with the old file
    with mock.patch('node_cli.core.nginx.nginx_answer', return_value='base 0000000000000000'):
        with pytest.raises(NginxConfigError):
            reload_nginx()
    assert read_base() == '# the base.conf nginx still runs\n'
    mock_reload.assert_called_once()


@pytest.mark.parametrize('previous', [None, '# the base.conf nginx still runs\n'])
@mock.patch('node_cli.core.nginx.check_ssl_certs', return_value=False)
@mock.patch('node_cli.core.nginx.docker_client')
@mock.patch('node_cli.core.nginx.reload_nginx_container')
def test_reload_nginx_with_config_nginx_rejects(
    mock_reload, mock_client, mock_ssl, fingerprint_template, previous
):
    os.makedirs(os.path.dirname(NGINX_BASE_CONFIG_FILEPATH), exist_ok=True)
    if previous is not None:
        Path(NGINX_BASE_CONFIG_FILEPATH).write_text(previous)
    mock_reload.side_effect = NginxConfigError('nginx -t failed')
    with pytest.raises(NginxConfigError, match='nginx -t failed'):
        reload_nginx()
    # the earlier file comes back, a first render stays for the next attempt
    assert read_base() == (previous or render_base_config(ssl_on=False, skale_node=True))


@mock.patch('node_cli.core.nginx.LOCK_TIMEOUT_SECONDS', 0.1)
@mock.patch('node_cli.core.nginx.docker_client')
@mock.patch('node_cli.core.nginx.reload_nginx_container')
def test_reload_nginx_waits_for_skale_admin_lock(mock_reload, mock_client, fingerprint_template):
    os.makedirs(NGINX_DIR, exist_ok=True)
    with FileLock(NGINX_LOCK_PATH), pytest.raises(NginxConfigError, match='nginx lock'):
        reload_nginx()
    mock_reload.assert_not_called()


@mock.patch('node_cli.core.ssl.upload.copy_cert_key_pair')
@mock.patch('node_cli.core.ssl.upload.check_cert_openssl')
@mock.patch('node_cli.core.ssl.upload.is_ssl_folder_empty', return_value=True)
def test_upload_cert_reports_certificates_nginx_does_not_serve(mock_empty, mock_check, mock_copy):
    with mock.patch(
        'node_cli.core.ssl.upload.reload_nginx', side_effect=NginxConfigError('kept old config')
    ):
        status, payload = upload_cert('cert.pem', 'key.pem', force=False)
    assert status == 'error'
    assert payload.startswith('Certificates are saved, but nginx is not serving them.')
    mock_copy.assert_called_once()


@mock.patch('node_cli.core.ssl.upload.copy_cert_key_pair')
@mock.patch('node_cli.core.ssl.upload.check_cert_openssl')
@mock.patch('node_cli.core.ssl.upload.is_ssl_folder_empty', return_value=True)
def test_upload_cert_opens_tls_ports_once_nginx_serves_them(mock_empty, mock_check, mock_copy):
    steps = mock.Mock()
    with (
        mock.patch('node_cli.core.ssl.upload.reload_nginx', steps.reload_nginx),
        mock.patch('node_cli.core.ssl.upload.sync_tls_ports', steps.sync_tls_ports),
    ):
        assert upload_cert('cert.pem', 'key.pem', force=False) == ('ok', None)
    assert steps.mock_calls == [mock.call.reload_nginx(), mock.call.sync_tls_ports()]

    steps.reset_mock()
    steps.reload_nginx.side_effect = NginxConfigError('kept old config')
    with (
        mock.patch('node_cli.core.ssl.upload.reload_nginx', steps.reload_nginx),
        mock.patch('node_cli.core.ssl.upload.sync_tls_ports', steps.sync_tls_ports),
    ):
        status, _ = upload_cert('cert.pem', 'key.pem', force=False)
    assert status == 'error'
    steps.sync_tls_ports.assert_not_called()


@mock.patch('node_cli.core.ssl.upload.copy_cert_key_pair')
@mock.patch('node_cli.core.ssl.upload.check_cert_openssl')
@mock.patch('node_cli.core.ssl.upload.is_ssl_folder_empty', return_value=True)
@mock.patch('node_cli.core.ssl.upload.reload_nginx')
def test_upload_cert_reports_firewall_that_was_not_updated(
    mock_reload, mock_empty, mock_check, mock_copy
):
    with mock.patch(
        'node_cli.core.ssl.upload.sync_tls_ports', side_effect=NFTablesError('not permitted')
    ):
        status, payload = upload_cert('cert.pem', 'key.pem', force=False)
    assert status == 'error'
    assert payload == (
        'Certificates are saved, but the firewall may still block the TLS ports. not permitted'
    )
