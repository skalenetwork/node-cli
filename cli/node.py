import os
import requests
import subprocess
from cli.config import INSTALL_SCRIPT
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


def init(git_branch, github_token, docker_username, docker_password, rpc_ip, rpc_port, db_user, db_password):
    # todo: show localhost message
    env = {
        **os.environ,
        'GIT_BRANCH': git_branch,
        'GITHUB_TOKEN': github_token,
        'DOCKER_USERNAME': docker_username,
        'DOCKER_PASSWORD': docker_password,
        'RPC_IP': rpc_ip,
        'RPC_PORT': rpc_port,
        'DB_USERNAME': db_user,
        'DB_PASSWORD': db_password,
    }
    res = subprocess.run(['bash', INSTALL_SCRIPT], env=env)
    # todo: check execution result
