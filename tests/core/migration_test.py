import pytest

from node_cli.migrations.focal_to_jammy import migrate, NFTablesManager

from node_cli.utils.helper import run_cmd

CUSTOM_CHAIN_NAME = 'TEST'


def add_base_rules():
    run_cmd(f'iptables -N {CUSTOM_CHAIN_NAME}'.split(' '))
    run_cmd('iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT'.split(' '))
    run_cmd('iptables -A INPUT -i lo -j ACCEPT'.split(' '))
    run_cmd('iptables -A INPUT -p tcp --dport 22 -j ACCEPT'.split(' '))
    run_cmd('iptables -A INPUT -p tcp --dport 8080 -j ACCEPT'.split(' '))
    run_cmd('iptables -A INPUT -p tcp --dport 443 -j ACCEPT'.split(' '))
    run_cmd('iptables -A INPUT -p tcp --dport 53 -j ACCEPT'.split(' '))
    run_cmd('iptables -A INPUT -p udp --dport 53 -j ACCEPT'.split(' '))
    run_cmd('iptables -A INPUT -p tcp --dport 3009 -j ACCEPT'.split(' '))
    # non skale related rule
    run_cmd(f'iptables -A {CUSTOM_CHAIN_NAME} -p tcp --dport 2222 -j ACCEPT'.split(' '))
    run_cmd('iptables -A INPUT -p tcp --dport 9100 -j ACCEPT'.split(' '))
    run_cmd('iptables -A INPUT -p tcp -j DROP'.split(' '))
    run_cmd('iptables -A INPUT -p udp -j DROP'.split(' '))
    run_cmd('iptables -I INPUT -p icmp --icmp-type destination-unreachable -j ACCEPT'.split(' '))
    run_cmd('iptables -I INPUT -p icmp --icmp-type source-quench -j ACCEPT'.split(' '))
    run_cmd('iptables -I INPUT -p icmp --icmp-type time-exceeded -j ACCEPT'.split(' '))


@pytest.fixture
def base_rules():
    try:
        add_base_rules()
        yield
    finally:
        run_cmd(['iptables', '-F'])


def test_migration(base_rules):
    migrate()
    res = run_cmd(['iptables', '-S'])
    output = res.stdout.decode('utf-8')
    assert output == f'-P INPUT ACCEPT\n-P FORWARD ACCEPT\n-P OUTPUT ACCEPT\n-N {CUSTOM_CHAIN_NAME}\n-A {CUSTOM_CHAIN_NAME} -p tcp -m tcp --dport 2222 -j ACCEPT\n'  # noqa
    nft = NFTablesManager(family='ip', table='filter')
    assert nft.get_rules(chain='INPUT') == []
