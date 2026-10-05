import os
import pwd
import stat
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock

import pytest
import requests_mock

from node_cli.utils import api_auth, helper


@pytest.fixture
def token_path(tmp_path, monkeypatch):
    path = tmp_path / '.skale' / 'auth' / 'admin-api.token'
    monkeypatch.setattr(api_auth, 'ADMIN_API_TOKEN_PATH', path)
    monkeypatch.setattr(api_auth, 'G_CONF_USER', pwd.getpwuid(os.geteuid()).pw_name)
    return path


def test_provisioning_preserves_token_and_restricts_permissions(token_path):
    api_auth.ensure_api_token()
    original = token_path.read_bytes()
    assert len(api_auth.read_api_token()) == 64
    assert stat.S_IMODE(token_path.stat().st_mode) == 0o600
    assert token_path.stat().st_uid == os.geteuid()
    assert stat.S_IMODE(token_path.parent.stat().st_mode) == 0o700
    assert token_path.parent.stat().st_uid == os.geteuid()
    api_auth.ensure_api_token()
    assert token_path.read_bytes() == original
    assert list(token_path.parent.iterdir()) == [token_path]


def test_existing_auth_directory_is_secured(token_path):
    api_auth.ensure_api_token()
    original = token_path.read_bytes()
    token_path.parent.chmod(0o755)
    api_auth.ensure_api_token()
    assert stat.S_IMODE(token_path.parent.stat().st_mode) == 0o700
    assert token_path.read_bytes() == original


def test_auth_directory_cannot_point_back_to_node_data(token_path):
    node_data = token_path.parent.parent / 'node_data'
    node_data.mkdir(parents=True)
    token_path.parent.symlink_to(node_data, target_is_directory=True)
    with pytest.raises(api_auth.APIAuthError):
        api_auth.ensure_api_token()
    assert list(node_data.iterdir()) == []


def test_concurrent_provisioning_publishes_one_complete_token(token_path):
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda _: api_auth.ensure_api_token(), range(16)))
    assert len(api_auth.read_api_token()) == 64
    assert list(token_path.parent.iterdir()) == [token_path]


@pytest.mark.parametrize('bad_file', ['empty', 'oversized', 'non_ascii', 'permissions', 'symlink'])
def test_invalid_credentials_are_not_replaced(token_path, bad_file):
    api_auth.ensure_api_token()
    if bad_file == 'permissions':
        token_path.chmod(0o644)
    elif bad_file == 'symlink':
        token_path.unlink()
        token_path.symlink_to(token_path.with_suffix('.missing'))
    else:
        token_path.write_text(
            {'empty': '', 'oversized': 'ab' * 32 + '\n\nmore', 'non_ascii': 'é'}[bad_file]
        )
    with pytest.raises(api_auth.APIAuthError):
        api_auth.ensure_api_token()


def test_missing_token_supports_upgrade_from_old_api(token_path):
    assert api_auth.get_api_headers() == {}
    with requests_mock.Mocker() as mock:
        mock.get(
            helper.construct_url('/api/v1/node/update-safe'), json={'status': 'ok', 'payload': {}}
        )
        assert helper.get_request('node', 'update-safe') == ('ok', {})
        assert 'Authorization' not in mock.last_request.headers
    assert not token_path.exists()


def test_headers_sent_for_get_post_and_upload(token_path):
    api_auth.ensure_api_token()
    expected = f'Bearer {api_auth.read_api_token()}'
    with requests_mock.Mocker() as mock:
        mock.get(
            helper.construct_url('/api/v1/node/signature'), json={'status': 'ok', 'payload': {}}
        )
        mock.post(
            helper.construct_url('/api/v1/wallet/send-eth'), json={'status': 'ok', 'payload': {}}
        )
        mock.post(helper.construct_url('/api/v1/ssl/upload'), json={'status': 'ok', 'payload': {}})
        assert helper.get_request('node', 'signature') == ('ok', {})
        assert helper.post_request('wallet', 'send-eth', json={'amount': 1}) == ('ok', {})
        assert helper.post_request('ssl', 'upload', files={'ssl_cert': ('cert', b'cert')}) == (
            'ok',
            {},
        )
        assert all(req.headers['Authorization'] == expected for req in mock.request_history)
        assert 'multipart/form-data' in mock.last_request.headers['Content-Type']


def test_http_errors_reach_cli(token_path):
    api_auth.ensure_api_token()
    with requests_mock.Mocker() as mock:
        mock.post(
            helper.construct_url('/api/v1/wallet/send-eth'),
            status_code=401,
            json={'status': 'error', 'payload': 'A valid node CLI credential is required'},
        )
        assert helper.post_request('wallet', 'send-eth') == (
            'error',
            'A valid node CLI credential is required',
        )


def test_does_not_follow_redirects_or_use_proxy_credentials(token_path, monkeypatch):
    api_auth.ensure_api_token()
    monkeypatch.setenv('HTTP_PROXY', 'http://proxy.invalid:8080')
    netrc = Mock(side_effect=AssertionError('Must not read netrc'))
    monkeypatch.setattr('requests.sessions.get_netrc_auth', netrc)
    with requests_mock.Mocker() as mock:
        mock.get(
            helper.construct_url('/api/v1/node/signature'),
            status_code=302,
            headers={'Location': 'http://other.invalid/steal'},
            json={'status': 'error', 'payload': 'Redirect'},
        )
        assert helper.get_request('node', 'signature') == ('error', 'Redirect')
        assert len(mock.request_history) == 1
        assert mock.last_request.proxies == {}
    netrc.assert_not_called()


def test_provisions_before_compose_starts(token_path, monkeypatch):
    from node_cli.utils import docker_utils
    from node_cli.utils.node_type import NodeMode, NodeType

    def run(cmd, env):
        assert api_auth.read_api_token() is not None

    start = Mock(side_effect=run)
    monkeypatch.setattr(docker_utils, 'run_cmd', start)
    settings = Mock(tg_api_key=None)
    docker_utils.compose_up({}, settings, NodeType.SKALE, NodeMode.ACTIVE)
    start.assert_called_once()


def test_invalid_token_prevents_starting_services(token_path, monkeypatch):
    from node_cli.utils import docker_utils
    from node_cli.utils.node_type import NodeMode, NodeType

    api_auth.ensure_api_token()
    token_path.chmod(0o644)
    start = Mock()
    monkeypatch.setattr(docker_utils, 'run_cmd', start)
    with pytest.raises(api_auth.APIAuthError):
        docker_utils.compose_up({}, Mock(), NodeType.SKALE, NodeMode.ACTIVE)
    start.assert_not_called()
