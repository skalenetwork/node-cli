import socket

import mock

from node_cli.core.iptables import allow_ssh, get_ssh_port


def test_get_ssh_port():
    assert get_ssh_port() == 22
    assert get_ssh_port('http') == 80
    with mock.patch.object(socket, 'getservbyname', side_effect=OSError):
        assert get_ssh_port() == 22


def test_allow_ssh():
    chain = mock.Mock()
    chain.rules = []
    allow_ssh(chain)
