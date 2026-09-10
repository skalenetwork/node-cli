import socket
import subprocess

import mock
import pytest

from node_cli.utils.helper import get_ssh_port, get_ssh_ports


@pytest.fixture(autouse=True)
def clear_ssh_override(monkeypatch):
    monkeypatch.delenv('SSH_PORT', raising=False)


def test_service_lookup_compatibility():
    assert get_ssh_port('http') == 80
    with mock.patch.object(socket, 'getservbyname', side_effect=OSError):
        assert get_ssh_port('missing-service') == 22


@pytest.mark.parametrize(
    'config,expected',
    [
        ('port 22\nlistenaddress 0.0.0.0:22\nlistenaddress [::]:22\n', [22]),
        ('port 2222\n', [2222]),
        ('port 2222\nport 2200\nport 2222\n', [2200, 2222]),
        ('port 22\nlistenaddress 192.0.2.1:2222\nlistenaddress [::1]:2200\n', [2200, 2222]),
    ],
)
def test_effective_sshd_ports(config, expected):
    with (
        mock.patch('node_cli.utils.helper.shutil.which', return_value='/usr/sbin/sshd'),
        mock.patch('node_cli.utils.helper.subprocess.run') as run,
    ):
        run.return_value.stdout = config
        assert get_ssh_ports() == expected
        run.assert_called_once_with(
            ['/usr/sbin/sshd', '-T'], capture_output=True, text=True, check=True, timeout=10
        )


def test_ssh_port_override(monkeypatch):
    monkeypatch.setenv('SSH_PORT', '2222')
    with mock.patch('node_cli.utils.helper.subprocess.run') as run:
        assert get_ssh_ports() == [2222]
        assert get_ssh_port() == 2222
        run.assert_not_called()


@pytest.mark.parametrize('value', ['', 'ssh', '0', '-1', '65536'])
def test_invalid_ssh_port_override(monkeypatch, value):
    monkeypatch.setenv('SSH_PORT', value)
    with pytest.raises(ValueError, match='SSH_PORT'):
        get_ssh_ports()


@pytest.mark.parametrize(
    'error',
    [
        FileNotFoundError(),
        subprocess.CalledProcessError(1, 'sshd'),
        subprocess.TimeoutExpired('sshd', 10),
    ],
)
def test_ssh_detection_failure_does_not_guess(error):
    with mock.patch('node_cli.utils.helper.subprocess.run', side_effect=error):
        with pytest.raises(RuntimeError, match='SSH_PORT'):
            get_ssh_port()


@pytest.mark.parametrize('config', ['', 'port invalid\n', 'port 65536\n'])
def test_invalid_sshd_output(config):
    with mock.patch('node_cli.utils.helper.subprocess.run') as run:
        run.return_value.stdout = config
        with pytest.raises(ValueError, match='SSH_PORT'):
            get_ssh_ports()
