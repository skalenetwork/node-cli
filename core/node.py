import os
import logging
import requests
import subprocess
from core.config import INSTALL_SCRIPT, UNINSTALL_SCRIPT, UPDATE_SCRIPT, UPDATE_NODE_PROJECT_SCRIPT
from core.config import URLS
from core.helper import get_node_creds, construct_url, post_request, print_err_response
from core.host import prepare_host
from core.resources import check_is_partition

logger = logging.getLogger(__name__)


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
        msg = 'Node registered in SKALE manager. For more info run: skale node info'
        logging.info(msg)
        print(msg)
    else:
        logging.info(response.json())
        print_err_response(response.json())


def init(mta_endpoint, git_branch, github_token, docker_username, docker_password, rpc_ip, rpc_port,
         db_user,
         db_password, db_root_password, db_port, disk_mountpoint, test_mode):
    env = {
        **os.environ,
        'MTA_ENDPOINT': mta_endpoint,
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
        'DISK_MOUNTPOINT': disk_mountpoint
    }

    if check_is_partition(disk_mountpoint):
        raise Exception("You provided partition path instead of disk mountpoint.")

    prepare_host(test_mode, disk_mountpoint)
    res = subprocess.run(['bash', INSTALL_SCRIPT], env=env)
    logging.info(f'Node init install script result: {res.stderr}, {res.stdout}')
    # todo: check execution result


def purge():
    # todo: check that node is installed
    res = subprocess.run(['sudo', 'bash', UNINSTALL_SCRIPT])
    # todo: check execution result


def deregister():
    pass


def update(mta_endpoint, github_token, docker_username, docker_password, rpc_ip, rpc_port, db_user,
           db_password,
           db_root_password, db_port):
    env = {
        **os.environ,
        'MTA_ENDPOINT': mta_endpoint,
        'GITHUB_TOKEN': github_token,
        'DOCKER_USERNAME': docker_username,
        'DOCKER_PASSWORD': str(docker_password),
        'RPC_IP': rpc_ip,
        'RPC_PORT': str(rpc_port),
        'DB_USER': db_user,
        'DB_PASSWORD': db_password,
        'DB_ROOT_PASSWORD': db_root_password,
        'DB_PORT': str(db_port),
        'DISK_MOUNTPOINT': '/',
        'RUN_MODE': 'prod'
    }
    res_update_project = subprocess.run(['sudo', '-E', 'bash', UPDATE_NODE_PROJECT_SCRIPT], env=env)
    logging.info(
        f'Update node project script result: {res_update_project.stderr}, {res_update_project.stdout}')
    res_update_node = subprocess.run(['sudo', '-E', 'bash', UPDATE_SCRIPT], env=env)
    logging.info(
        f'Update node script result: {res_update_node.stderr}, {res_update_node.stdout}')
    # todo: check execution result
