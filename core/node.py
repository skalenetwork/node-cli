import os
import requests
import subprocess
from core.config import INSTALL_SCRIPT, UNINSTALL_SCRIPT
from core.config import URLS
from core.helper import get_node_creds, construct_url, post_request, print_err_response


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
    response = post_request(url, data, cookies)
    if response is None:
        return None
    if response.status_code == requests.codes.created:
        print('Node registered in SKALE manager. For more info run: skale node info')
    else:
        print_err_response(response.json())


def init(git_branch, github_token, docker_username, docker_password, rpc_ip, rpc_port, db_user,
         db_password, db_root_password, db_port):
    # todo: show localhost message
    env = {
        **os.environ,
        'GIT_BRANCH': git_branch,
        'GITHUB_TOKEN': github_token,
        'DOCKER_USERNAME': docker_username,
        'DOCKER_PASSWORD': str(docker_password),
        'RPC_IP': rpc_ip,
        'RPC_PORT': str(rpc_port),
        'DB_USER': db_user,
        'DB_PASSWORD': db_password,
        'DB_ROOT_PASSWORD': db_root_password,
        'DB_PORT': str(db_port),
        'DISK_MOUNTPOINT': '/'
    }
    res = subprocess.run(['bash', INSTALL_SCRIPT], env=env)
    # todo: check execution result


def purge():
    # todo: check that node is installed
    res = subprocess.run(['sudo', 'bash', UNINSTALL_SCRIPT])
    # todo: check execution result
