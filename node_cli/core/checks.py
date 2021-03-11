#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
#
#   Copyright (C) 2019 SKALE Labs
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.


import inspect
import json
import logging
import os
import psutil
import shutil
import socket
from collections import namedtuple
from typing import List

import docker
import yaml

from node_cli.configs import DOCKER_CONFIG_FILEPATH, REQUIREMENTS_PATH
from node_cli.utils.helper import run_cmd

logger = logging.getLogger(__name__)


CheckResult = namedtuple('CheckResult', ['name', 'status', 'info'])
ListChecks = List[CheckResult]


def get_requirements(network: str = 'mainnet'):
    with open(REQUIREMENTS_PATH) as requirements_file:
        ydata = yaml.load(requirements_file, Loader=yaml.Loader)
        logger.info(ydata)
        return ydata[network]


class BaseChecker:
    def _ok(self, name: str, info=None) -> CheckResult:
        return CheckResult(name=name, status='ok', info=info)

    def _error(self, name: str, info=None) -> CheckResult:
        return CheckResult(name=name, status='error', info=info)

    def check(self) -> ListChecks:
        myself = inspect.stack()[0][3]
        check_methods = inspect.getmembers(
            type(self),
            predicate=lambda m: inspect.isfunction(m) and
            not m.__name__.startswith('_') and not m.__name__ == myself
        )
        return [cm[1](self) for cm in check_methods]


class MachineChecker(BaseChecker):
    def __init__(self, requirements: dict) -> None:
        self.requirements = requirements

    def cpu_total(self) -> CheckResult:
        name = 'cpu_total'
        actual = psutil.cpu_count(logical=True)
        expected = self.requirements['hardware']['cpu_total']
        info = f'Expected {expected} logical cores, actual {actual} cores'
        if actual < expected:
            return self._error(name=name, info=info)
        else:
            return self._ok(name=name, info=info)

    def cpu_physical(self) -> CheckResult:
        name = 'cpu_physical'
        actual = psutil.cpu_count(logical=False)
        expected = self.requirements['hardware']['cpu_physical']
        info = f'Expected {expected} physical cores, actual {actual} cores'
        if actual < expected:
            return self._error(name=name, info=info)
        else:
            return self._ok(name=name, info=info)

    def memory(self) -> CheckResult:
        name = 'memory'
        actual = psutil.virtual_memory().total,
        actual = actual[0]
        expected = self.requirements['hardware']['memory']
        actual_gb = round(actual / 1024 ** 3, 2)
        expected_gb = round(expected / 1024 ** 3, 2)
        info = f'Expected RAM {expected_gb} GB, actual {actual_gb} GB'
        if actual < expected:
            return self._error(name=name, info=info)
        else:
            return self._ok(name=name, info=info)

    def swap(self) -> CheckResult:
        name = 'swap'
        actual = psutil.swap_memory().total
        expected = self.requirements['hardware']['swap']
        actual_gb = round(actual / 1024 ** 3, 2)
        expected_gb = round(expected / 1024 ** 3, 2)
        info = f'Expected swap memory {expected_gb} GB, actual {actual_gb} GB'
        if actual < expected:
            return self._error(name=name, info=info)
        else:
            return self._ok(name=name, info=info)

    def network(self) -> CheckResult:
        name = 'network'
        timeout = 4
        cloudflare_dns_host = '1.1.1.1'
        cloudflare_dns_host_port = 443
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(
                (cloudflare_dns_host, cloudflare_dns_host_port))
            return self._ok(name=name)
        except socket.error as err:
            info = f'Network checking returned error: {err}'
            return self._error(name=name, info=info)


class PackagesChecker(BaseChecker):
    def __init__(self, requirements: dict) -> None:
        self.requirements = requirements

    def _compose_get_binary_cmd(self, binary_name: str) -> list:
        return ['command', '-v', binary_name]

    def docker(self) -> CheckResult:
        name = 'docker package'
        cmd = shutil.which('docker')
        if cmd is None:
            info = 'No such command: "docker"'
            return self._error(name=name, info=info)

        v_cmd_result = run_cmd(['docker', '-v'], check_code=False)
        output = v_cmd_result.stdout.decode('utf-8')
        if v_cmd_result.returncode == 0:
            return self._ok(name=name, info=output)
        else:
            return self._error(name=name, info=output)

    def docker_compose(self) -> CheckResult:
        name = 'docker-compose'
        cmd = shutil.which('docker-compose')
        if cmd is None:
            info = 'No such command: "docker-compose"'
            return self._error(name=name, info=info)

        v_cmd_result = run_cmd(['docker-compose', '-v'], check_code=False)
        output = v_cmd_result.stdout.decode('utf-8')
        if v_cmd_result.returncode != 0:
            output = v_cmd_result.stdout.decode('utf-8')
            info = f'Checking docker-compose version failed with: {output}'
            return self._error(name=name, info=output)

        actual_version = output.split(',')[0].split()[-1].strip()
        expected_version = self.requirements['packages']['docker-compose']
        info = {
            'expected_version': expected_version,
            'actual_version': actual_version
        }
        info = f'Expected docker-compose version {expected_version}, actual {actual_version}'
        if actual_version < expected_version:
            return self._error(name=name, info=info)
        else:
            return self._ok(name=name, info=info)

    def iptables_persistent(self) -> CheckResult:
        name = 'iptables-persistent'
        dpkg_cmd_result = run_cmd(
            ['dpkg', '-s', 'iptables-persistent'], check_code=False)
        output = dpkg_cmd_result.stdout.decode('utf-8')
        if dpkg_cmd_result.returncode == 0:
            return self._ok(name=name, info=output)
        else:
            return self._error(name=name, info=output)

    def lvm2(self) -> CheckResult:
        name = 'lvm2'
        dpkg_cmd_result = run_cmd(
            ['dpkg', '-s', 'lvm2'], check_code=False)
        output = dpkg_cmd_result.stdout.decode('utf-8')
        if dpkg_cmd_result.returncode == 0:
            return self._ok(name=name, info=output)
        else:
            return self._error(name=name, info=output)


class DockerChecker(BaseChecker):
    def __init__(self) -> None:
        self.docker_client = docker.from_env()

    def _get_docker_config(self) -> dict:
        if not os.path.isfile(DOCKER_CONFIG_FILEPATH):
            logger.error(f'No such file {DOCKER_CONFIG_FILEPATH}')
            return {}
        with open(DOCKER_CONFIG_FILEPATH) as docker_config_file:
            try:
                docker_config = json.load(docker_config_file)
            except json.decoder.JSONDecodeError as err:
                logger.error(f'Loading docker config json failed with {err}')
                return {}
            return docker_config

    def _check_docker_alive_option(self, config: dict) -> tuple:
        actual_value = config.get('live-restore', None)
        expected_value = True
        if actual_value != expected_value:
            info = (
                'Docker daemon live-restore option '
                'should be set as "true"'
            )
            return False, info
        else:
            info = 'Docker daemon live-restore option is set as "true"'
            return True, info

    def keeping_containers_alive(self) -> CheckResult:
        name = 'live-restore'
        config = self._get_docker_config()
        is_ok, info = self._check_docker_alive_option(config)
        if is_ok:
            return self._ok(name=name, info=info)
        else:
            return self._error(name=name, info=info)

    def docker_service_status(self) -> CheckResult:
        name = 'docker service status'
        try:
            self.docker_client.containers.list()
        except Exception as err:
            info = err
            return self._error(name=name, info=info)
        return self._ok(name=name)
