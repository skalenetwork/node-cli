import inspect
import json
import logging
import os
import psutil
import socket
from collections import namedtuple
from typing import List

import docker
import yaml

from configs import REQUIREMENTS_PATH
from tools.helper import run_cmd

logger = logging.getLogger(__name__)


CheckResult = namedtuple('CheckResult', ['status', 'info'])
ListChecks = List[CheckResult]

DOCKER_CONFIG_FILEPATH = '/etc/docker/daemon.json'


def get_requirements():
    return yaml.load(REQUIREMENTS_PATH)


class BaseChecker:
    def __init__(self) -> None:
        pass

    def _ok(self, info=None) -> CheckResult:
        return CheckResult(status='ok', info=info)

    def _error(self, info=None) -> CheckResult:
        return CheckResult(status='error', info=info)

    def check(self) -> ListChecks:
        check_methods = inspect.getmembers(
            type(self),
            predicate=lambda x: inspect.isfunction(x) and
            not x.__name__.startswith('_')
        )
        return [cm() for cm in check_methods]


class MachineChecker(BaseChecker):
    def __init__(self, requirements: dict) -> None:
        self.requirements = requirements

    def cpu_total(self) -> CheckResult:
        actual = psutil.cpu_count(logical=True)
        expected = self.requirements['hardware']['cpu_total']
        info = {
            'actual_cpu_total': actual,
            'excpected_cpu_total': expected
        }
        if actual < expected:
            return self._error(info=info)
        else:
            return self._ok(info=info)

    def cpu_physical(self) -> CheckResult:
        actual = psutil.cpu_count(logical=False)
        expected = self.requirements['hardware']['cpu_physical']
        info = {
            'actual_cpu_physical': actual,
            'expected_cpu_physical': expected
        }
        if actual < expected:
            return self._error(info=info)
        else:
            return self._ok(info=info)

    def memory(self) -> CheckResult:
        actual = psutil.virtual_memory().total,
        actual = actual[0]
        expected = self.requirements['hardware']['memory']
        info = {
            'actual_memory': actual,
            'expected_memory': expected
        }
        if actual < expected:
            return self._error(info=info)
        else:
            return self._ok(info=info)

    def swap(self) -> CheckResult:
        actual = psutil.swap_memory().total
        expected = self.requirements['hardware']['swap']
        info = {
            'actual_swap': actual,
            'expected_swap': expected
        }
        if actual < expected:
            return self._error(info=info)
        else:
            return self._ok(info=info)

    def network(self) -> CheckResult:
        timeout = 4
        cloudflare_dns_host = '1.1.1.1'
        cloudflare_dns_host_port = 443
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(
                (cloudflare_dns_host, cloudflare_dns_host_port))
            return self._ok()
        except socket.error as err:
            info = {
                'socket_error': str(err)
            }
            return self._error(info=info)


class PackagesChecker(BaseChecker):
    def __init__(self, requirements: dict) -> None:
        self.requirements = requirements

    def docker(self) -> CheckResult:
        which_cmd_result = run_cmd(['which', 'docker'], check_code=False)
        if which_cmd_result.returncode != 0:
            output = which_cmd_result.stdout.decode('utf-8')
            return self._error(info=output)

        v_cmd_result = run_cmd(['docker', '-v'], check_code=False)
        output = v_cmd_result.stdout.decode('utf-8')
        if v_cmd_result.returncode == 0:
            return self._ok(info=output)
        else:
            return self._error(output)

    def docker_compose(self) -> CheckResult:
        which_cmd_result = run_cmd(
            ['which', 'docker-compose'], check_code=False)
        if which_cmd_result.returncode != 0:
            info = which_cmd_result.stdout.decode('utf-8')
            return self._error(info=info)

        v_cmd_result = run_cmd(['docker-compose', '-v'], check_code=False)
        output = v_cmd_result.stdout.decode('utf-8')
        if v_cmd_result.returncode != 0:
            return self._error(info=output)
        actual_version = output.split(',')[0].split()[-1].strip()
        expected_version = self.requirements['packages']['docker-compose']
        info = {
            'expected_version': expected_version,
            'actual_version': actual_version
        }
        if actual_version < expected_version:
            return self._error(info)
        else:
            return self._ok(info)

    def iptables_persistent(self) -> CheckResult:
        dpkg_cmd_result = run_cmd(
            ['dpkg', '-s', 'iptables-persistent'], check_code=False)
        output = dpkg_cmd_result.stdout.decode('utf-8')
        if dpkg_cmd_result.returncode == 0:
            return self._ok(info=output)
        else:
            return self._error(info=output)

    def lvm2(self) -> CheckResult:
        dpkg_cmd_result = run_cmd(
            ['dpkg', '-s', 'lvm2'], check_code=False)
        output = dpkg_cmd_result.stdout.decode('utf-8')
        if dpkg_cmd_result.returncode == 0:
            return self._ok(output)
        else:
            return self._error(info=output)


class DockerChecker:
    def __init__(self, requirements: dict) -> None:
        self.docker_client = docker.from_env()

    def _get_docker_config(self) -> dict:
        if not os.path.isfile(DOCKER_CONFIG_FILEPATH):
            logger.error(f'No such file {DOCKER_CONFIG_FILEPATH}')
            return {}
        with open(DOCKER_CONFIG_FILEPATH) as docker_config_file:
            try:
                docker_config = json.load(docker_config_file)
            except json.JSONDecoderError as err:
                logger.error(f'Loading docker config json failed with {err}')
                return {}
            return docker_config

    def _check_docker_alive_option(self, config: dict) -> CheckResult:
        actual_value = config.get('live-restore', None)
        expected_value = True
        info = {
            'actual_value': actual_value,
            'expected_value': expected_value
        }
        if actual_value != expected_value:
            return self._error(info=info)
        else:
            return self._ok(info=info)

    def keeping_containers_alive(self) -> CheckResult:
        config = self.get_docker_config()
        return self.check_docker_alive_option(config)

    def docker_service_status(self) -> CheckResult:
        try:
            self.docker_client.contianers.list()
        except Exception as err:
            info = err
            return self._error(info=info)
        return self._ok()
