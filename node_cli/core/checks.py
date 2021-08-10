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
from functools import wraps
from typing import Dict, List, Optional, Tuple

import docker
import yaml
from debian import debian_support
from packaging.version import parse as version_parse

from node_cli.configs import (
    DOCKER_CONFIG_FILEPATH,
    DOCKER_DAEMON_HOSTS,
    ENVIRONMENT_PARAMS_FILEPATH,
    CHECK_REPORT_PATH
)
from node_cli.utils.helper import run_cmd

logger = logging.getLogger(__name__)


CheckResult = namedtuple('CheckResult', ['name', 'status', 'info'])
ListChecks = List[CheckResult]


NETWORK_CHECK_TIMEOUT = 4
CLOUDFLARE_DNS_HOST = '1.1.1.1'
CLOUDFLARE_DNS_HOST_PORT = 443


def get_env_params(network: str = 'mainnet'):
    with open(ENVIRONMENT_PARAMS_FILEPATH) as requirements_file:
        ydata = yaml.load(requirements_file, Loader=yaml.Loader)
        return ydata['envs'][network]


def node_check(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as err:
            logger.exception('%s check errored')
            return CheckResult(
                name=func.__name__,
                status='error',
                info=repr(err)
            )
    return wrapper


def generate_report_from_checks(checks_result: List[CheckResult]) -> Dict:
    report = [
        {'name': cr.name, 'status': cr.status}
        for cr in checks_result
    ]
    return report


def save_report(report: Dict):
    with open(CHECK_REPORT_PATH, 'w') as report_file:
        json.dump(report, report_file)


class BaseChecker:
    def _ok(self, name: str, info: Optional[Dict] = None) -> CheckResult:
        return CheckResult(name=name, status='ok', info=info)

    def _failed(self, name: str, info: Optional[Dict] = None) -> CheckResult:
        return CheckResult(name=name, status='failed', info=info)

    def check(self) -> ListChecks:
        myself = inspect.stack()[0][3]
        check_methods = inspect.getmembers(
            type(self),
            predicate=lambda m: inspect.isfunction(m) and
            not m.__name__.startswith('_') and not m.__name__ == myself
        )
        return [cm[1](self) for cm in check_methods]


class MachineChecker(BaseChecker):
    def __init__(self, requirements: Dict) -> None:
        self.requirements = requirements

    @node_check
    def cpu_total(self) -> CheckResult:
        name = 'cpu-total'
        actual = psutil.cpu_count(logical=True)
        expected = self.requirements['cpu_total']
        info = f'Expected {expected} logical cores, actual {actual} cores'
        if actual < expected:
            return self._failed(name=name, info=info)
        else:
            return self._ok(name=name, info=info)

    @node_check
    def cpu_physical(self) -> CheckResult:
        name = 'cpu-physical'
        actual = psutil.cpu_count(logical=False)
        expected = self.requirements['cpu_physical']
        info = f'Expected {expected} physical cores, actual {actual} cores'
        if actual < expected:
            return self._failed(name=name, info=info)
        else:
            return self._ok(name=name, info=info)

    @node_check
    def memory(self) -> CheckResult:
        name = 'memory'
        actual = psutil.virtual_memory().total,
        actual = actual[0]
        expected = self.requirements['memory']
        actual_gb = round(actual / 1024 ** 3, 2)
        expected_gb = round(expected / 1024 ** 3, 2)
        info = f'Expected RAM {expected_gb} GB, actual {actual_gb} GB'
        if actual < expected:
            return self._failed(name=name, info=info)
        else:
            return self._ok(name=name, info=info)

    @node_check
    def swap(self) -> CheckResult:
        name = 'swap'
        actual = psutil.swap_memory().total
        expected = self.requirements['swap']
        actual_gb = round(actual / 1024 ** 3, 2)
        expected_gb = round(expected / 1024 ** 3, 2)
        info = f'Expected swap memory {expected_gb} GB, actual {actual_gb} GB'
        if actual < expected:
            return self._failed(name=name, info=info)
        else:
            return self._ok(name=name, info=info)

    @node_check
    def network(self) -> CheckResult:
        name = 'network'
        try:
            socket.setdefaulttimeout(NETWORK_CHECK_TIMEOUT)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(
                (CLOUDFLARE_DNS_HOST, CLOUDFLARE_DNS_HOST_PORT))
            return self._ok(name=name)
        except socket.error as err:
            info = f'Network checking returned error: {err}'
            return self._failed(name=name, info=info)


class PackagesChecker(BaseChecker):
    def __init__(self, requirements: Dict) -> None:
        self.requirements = requirements

    @node_check
    def iptables_persistent(self) -> CheckResult:
        return self._check_apt_package('iptables-persistent')

    @node_check
    def lvm2(self) -> CheckResult:
        return self._check_apt_package('lvm2')

    @node_check
    def btrfs_progs(self) -> CheckResult:
        return self._check_apt_package('btrfs-progs')

    @node_check
    def lsof(self) -> CheckResult:
        return self._check_apt_package('lsof')

    @node_check
    def psmisc(self) -> CheckResult:
        return self._check_apt_package('psmisc')

    def _version_from_dpkg_output(self, output: str) -> str:
        info_lines = map(lambda s: s.strip(), output.split('\n'))
        v_line = next(filter(
            lambda s: s.startswith('Version'),
            info_lines
        ))
        return v_line.split()[1]

    def _check_apt_package(self, package_name: str,
                           version: str = None) -> CheckResult:
        # TODO: check versions
        dpkg_cmd_result = run_cmd(
            ['dpkg', '-s', package_name], check_code=False)
        output = dpkg_cmd_result.stdout.decode('utf-8').strip()
        if dpkg_cmd_result.returncode != 0:
            return self._failed(name=package_name, info=output)

        actual_version = self._version_from_dpkg_output(output)
        expected_version = self.requirements[package_name]
        info = {
            'expected_version': expected_version,
            'actual_version': actual_version
        }
        compare_result = debian_support.version_compare(
            actual_version, expected_version
        )
        if compare_result == -1:
            return self._failed(name=package_name, info=info)
        else:
            return self._ok(name=package_name, info=info)


class DockerChecker(BaseChecker):
    def __init__(self, requirements: Dict) -> None:
        self.docker_client = docker.from_env()
        self.requirements = requirements

    def _check_docker_command(self) -> str:
        return shutil.which('docker')

    def _get_docker_version_info(self) -> Dict:
        try:
            return self.docker_client.version()
        except Exception as err:
            logger.error(f'Request to docker api failed {err}')

    @node_check
    def docker_engine(self) -> CheckResult:
        name = 'docker-engine'
        if self._check_docker_command() is None:
            return self._failed(name=name, info='No such command: "docker"')

        version_info = self._get_docker_version_info()
        if not version_info:
            return self._failed(
                name=name,
                info='Docker api request failed. Is docker installed?'
            )
        logger.info('Docker version info %s', version_info)
        actual_version = self.docker_client.version()['Version']
        expected_version = self.requirements['docker-engine']
        info = {
            'expected_version': expected_version,
            'actual_version': actual_version
        }
        if version_parse(actual_version) < version_parse(expected_version):
            return self._failed(name=name, info=info)
        else:
            return self._ok(name=name, info=info)

    @node_check
    def docker_api(self) -> CheckResult:
        name = 'docker-api'
        if self._check_docker_command() is None:
            return self._failed(name=name, info='No such command: "docker"')

        version_info = self._get_docker_version_info()
        if not version_info:
            return self._failed(
                name=name,
                info='Docker api request failed. Is docker installed?'
            )
        logger.info('Docker version info %s', version_info)
        actual_version = version_info['ApiVersion']
        expected_version = self.requirements['docker-api']
        info = {
            'expected_version': expected_version,
            'actual_version': actual_version
        }
        if version_parse(actual_version) < version_parse(expected_version):
            return self._failed(name=name, info=info)
        else:
            return self._ok(name=name, info=info)

    @node_check
    def docker_compose(self) -> CheckResult:
        name = 'docker-compose'
        cmd = shutil.which('docker-compose')
        if cmd is None:
            info = 'No such command: "docker-compose"'
            return self._failed(name=name, info=info)

        v_cmd_result = run_cmd(['docker-compose', '-v'], check_code=False)
        output = v_cmd_result.stdout.decode('utf-8').rstrip()
        if v_cmd_result.returncode != 0:
            output = v_cmd_result.stdout.decode('utf-8')
            info = f'Checking docker-compose version failed with: {output}'
            return self._failed(name=name, info=output)

        actual_version = output.split(',')[0].split()[-1].strip()
        expected_version = self.requirements['docker-compose']

        info = {
            'expected_version': expected_version,
            'actual_version': actual_version
        }
        info = f'Expected docker-compose version {expected_version}, actual {actual_version}'  # noqa
        if version_parse(actual_version) < version_parse(expected_version):
            return self._failed(name=name, info=info)
        else:
            return self._ok(name=name, info=info)

    def _get_docker_config(self) -> Dict:
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

    def _check_docker_alive_option(self, config: Dict) -> Tuple:
        actual_value = config.get('live-restore', None)
        if actual_value is not True:
            info = (
                'Docker daemon live-restore option '
                'should be set as "true"'
            )
            return False, info
        else:
            info = 'Docker daemon live-restore option is set as "true"'
            return True, info

    def _check_docker_hosts_option(self, config: Dict) -> Tuple:
        actual_value = config.get('hosts', None)
        sactual, sexpected = set(actual_value), set(DOCKER_DAEMON_HOSTS)
        print(sactual, sexpected)
        if sactual & sexpected != sexpected:
            missing = sorted(sexpected - sactual)
            info = f'Docker daemon hosts is misconfigured. Missing hosts: {missing}'
            return False, info
        else:
            info = 'Hosts is properly configured'
            return True, info

    @node_check
    def keeping_containers_alive(self) -> CheckResult:
        name = 'live-restore'
        config = self._get_docker_config()
        is_ok, info = self._check_docker_alive_option(config)
        if is_ok:
            return self._ok(name=name, info=info)
        else:
            return self._failed(name=name, info=info)

    @node_check
    def hosts_config(self) -> CheckResult:
        name = 'docker-hosts'
        config = self._get_docker_config()
        is_ok, info = self._check_docker_hosts_option(config)
        if is_ok:
            return self._ok(name=name, info=info)
        else:
            return self._failed(name=name, info=info)
