import logging

from node_cli.utils.helper import get_ssh_port, run_cmd

logger = logging.getLogger(__name__)


ALLOWED_INCOMING_TCP_PORTS = [
    '80',  # filestorage
    '311',  # watchdog https
    '8080',  # http
    '443',  # https
    '53',  # dns
    '3009',  # watchdog http
    '9100'  # node exporter
]

ALLOWED_INCOMING_UDP_PORTS = [
    '53'  # dns
]


def remove_tcp_rules(ssh_port: int) -> None:
    tcp_rule_template = 'iptables -{} INPUT -p tcp -m tcp --dport {} -j ACCEPT'
    for tcp_port in [*ALLOWED_INCOMING_TCP_PORTS, ssh_port]:
        check_cmd = tcp_rule_template.format('C', tcp_port).split(' ')
        remove_cmd = tcp_rule_template.format('D', tcp_port).split(' ')
        result = run_cmd(check_cmd, check_code=False)
        if result.returncode == 0:
            result = run_cmd(remove_cmd)


def remove_udp_rules() -> None:
    udp_rule_template = 'iptables -{} INPUT -p udp -m udp --dport {} -j ACCEPT'
    for udp_port in [*ALLOWED_INCOMING_UDP_PORTS]:
        check_cmd = udp_rule_template.format('C', udp_port).split(' ')
        remove_cmd = udp_rule_template.format('D', udp_port).split(' ')
        result = run_cmd(check_cmd, check_code=False)
        if result.returncode == 0:
            result = run_cmd(remove_cmd)


def remove_loopback_rules() -> None:
    loopback_rule_template = 'iptables -{} INPUT -i lo -j ACCEPT'
    check_cmd = loopback_rule_template.format('C').split(' ')
    remove_cmd = loopback_rule_template.format('D').split(' ')
    result = run_cmd(check_cmd, check_code=False)
    if result.returncode == 0:
        result = run_cmd(remove_cmd)


def remove_icmp_rules() -> None:
    icmp_rule_template = 'iptables -{} INPUT -p icmp -m icmp --icmp-type {} -j ACCEPT'
    for icmp_type in [3, 4, 11]:
        check_cmd = icmp_rule_template.format('C', icmp_type).split(' ')
        remove_cmd = icmp_rule_template.format('D', icmp_type).split(' ')
        result = run_cmd(check_cmd, check_code=False)
        if result.returncode == 0:
            result = run_cmd(remove_cmd)


def remove_conntrack_rules() -> None:
    track_rule_template = 'iptables -{} INPUT -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT'
    check_cmd = track_rule_template.format('C').split(' ')
    remove_cmd = track_rule_template.format('D').split(' ')
    result = run_cmd(check_cmd, check_code=False)
    if result.returncode == 0:
        result = run_cmd(remove_cmd)


def remove_drop_rules() -> None:
    drop_rule_template = 'iptables -{} INPUT -p {} -j DROP'
    protocols = ['tcp', 'udp']
    for proto in protocols:
        check_cmd = drop_rule_template.format('C', proto).split(' ')
        remove_cmd = drop_rule_template.format('D', proto).split(' ')
        result = run_cmd(check_cmd, check_code=False)
        if result.returncode == 0:
            result = run_cmd(remove_cmd)


def remove_old_firewall_rules(ssh_port: int) -> None:
    remove_drop_rules()
    remove_conntrack_rules()
    remove_loopback_rules()
    remove_udp_rules()
    remove_tcp_rules(ssh_port)
    remove_icmp_rules()


def migrate() -> None:
    ssh_port = get_ssh_port()
    logger.info('Running migration from focal to jammy')
    remove_old_firewall_rules(ssh_port)
    logger.info('Migration from focal to jammy completed')
