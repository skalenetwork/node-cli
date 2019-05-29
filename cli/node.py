import requests
import os
import paramiko
from cli.config import URLS
from cli.helper import get_node_creds, construct_url


def create_node(config, name, p2p_ip, public_ip, port):
    # todo: add name, ips and port checks
    host, cookies = get_node_creds(config)
    data = {
        'name': name,
        'ip': p2p_ip,
        'publicIP': public_ip,
        'port': port
    }
    url = construct_url(host, URLS['create_node'])
    response = requests.post(url, json=data, cookies=cookies)

    print(response.text)


def init_node(ip, ssh_username, git_branch, github_token, docker_username, docker_password, rpc_ip, rpc_port, db_user,
              db_password, ssh_port=22, ssh_password=None):

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    client.connect(ip, port=ssh_port, username=ssh_username, password=ssh_password)
    stdin, stdout, stderr = client.exec_command('whoami')

    for line in stdout:
        print('... ' + line.strip('\n'))
    client.close()
