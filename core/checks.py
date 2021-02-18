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

from configs import DOCKER_CONFIG_FILEPATH, REQUIREMENTS_PATH
from tools.helper import run_cmd

logger = logging.getLogger(__name__)


CheckResult = namedtuple('CheckResult', ['status', 'info'])
ListChecks = List[CheckResult]


def get_requirements(network: str = 'mainnet'):
    return yaml.load(REQUIREMENTS_PATH)[network]


class BaseChecker:
    def _ok(self, info=None) -> CheckResult:
        return CheckResult(status='ok', info=info)

    def _error(self, info=None) -> CheckResult:
        return CheckResult(status='error', info=info)

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

    def _compose_get_binary_cmd(self, binary_name: str) -> list:
        return ['command', '-v', binary_name]

    def docker(self) -> CheckResult:
        cmd = shutil.which('docker')
        if cmd is None:
            info = 'No such command: "docker"'
            return self._error(info=info)

        v_cmd_result = run_cmd(['docker', '-v'], check_code=False)
        output = v_cmd_result.stdout.decode('utf-8')
        if v_cmd_result.returncode == 0:
            return self._ok(info=output)
        else:
            return self._error(output)

    def docker_compose(self) -> CheckResult:
        cmd = shutil.which('docker-compose')
        if cmd is None:
            info = 'No such command: "docker-compose"'
            return self._error(info=info)

        v_cmd_result = run_cmd(['docker-compose', '-v'], check_code=False)
        output = v_cmd_result.stdout.decode('utf-8')
        if v_cmd_result.returncode != 0:
            output = v_cmd_result.stdout.decode('utf-8')
            info = f'Checking docker-compose version failed with: {output}'
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
        config = self._get_docker_config()
        return self._check_docker_alive_option(config)

    def docker_service_status(self) -> CheckResult:
        try:
            self.docker_client.contianers.list()
        except Exception as err:
            info = err
            return self._error(info=info)
        return self._ok()
