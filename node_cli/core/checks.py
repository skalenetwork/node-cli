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


import enum
import functools
import inspect
import itertools
import json
import logging
import os
import shutil
import socket
from collections import namedtuple
from functools import wraps
from typing import (
    Any, Callable, cast,
    Dict, Iterable, Iterator,
    List, Optional,
    Tuple, TypeVar, Union, )

import docker  # type: ignore
import psutil  # type: ignore
import yaml
from debian import debian_support
from packaging.version import parse as version_parse

from node_cli.configs import (
    CHECK_REPORT_PATH,
    CONTAINER_CONFIG_PATH,
    DOCKER_CONFIG_FILEPATH,
    DOCKER_DAEMON_HOSTS,
    REPORTS_PATH,
    STATIC_PARAMS_FILEPATH
)
from node_cli.core.resources import get_disk_size
from node_cli.utils.helper import run_cmd, safe_mkdir

logger = logging.getLogger(__name__)


CheckResult = namedtuple('CheckResult', ['name', 'status', 'info'])
ResultList = List[CheckResult]


NETWORK_CHECK_TIMEOUT = 4
CLOUDFLARE_DNS_HOST = '1.1.1.1'
CLOUDFLARE_DNS_HOST_PORT = 443

Func = TypeVar('Func', bound=Callable[..., Any])
FuncList = List[Func]


def get_static_params(
    env_type: str = 'mainnet',
    config_path: str = CONTAINER_CONFIG_PATH
) -> Dict:
    status_params_filename = os.path.basename(STATIC_PARAMS_FILEPATH)
    static_params_filepath = os.path.join(config_path, status_params_filename)
    with open(static_params_filepath) as requirements_file:
        ydata = yaml.load(requirements_file, Loader=yaml.Loader)
        return ydata['envs'][env_type]


def check_quietly(check: Func, *args, **kwargs) -> CheckResult:
    try:
        return check(*args, **kwargs)
    except Exception as err:
        logger.exception('%s check errored')
        return CheckResult(
            name=check.__name__,
            status='error',
            info=repr(err)
        )


class CheckType(enum.Enum):
    PREINSTALL = 1
    POSTINSTALL = 2
    ALL = 3


def preinstall(func) -> Func:
    func._check_type = CheckType.PREINSTALL

    @wraps(func)
    def wrapper(*args, **kwargs) -> CheckResult:
        return check_quietly(func, *args, **kwargs)

    return cast(Func, wrapper)


def postinstall(func) -> Func:
    func._check_type = CheckType.POSTINSTALL

    @wraps(func)
    def wrapper(*args, **kwargs) -> CheckResult:
        return check_quietly(func, *args, **kwargs)

    return cast(Func, wrapper)


def generate_report_from_result(
    check_result: List[CheckResult]
) -> List[Dict]:
    report = [
        {'name': cr.name, 'status': cr.status}
        for cr in check_result
    ]
    return report


def dedup(seq: Iterable, key: Optional[Func] = None) -> Iterator:
    seen = set()
    for item in seq:
        e = item if key is None else key(item)
        if e not in seen:
            yield item
            seen.add(e)


def get_report(report_path: str = CHECK_REPORT_PATH) -> List[Dict]:
    saved_report = []
    if os.path.isfile(report_path):
        with open(report_path) as report_file:
            saved_report = json.load(report_file)
    return saved_report


def save_report(
    new_report: List[Dict],
    report_path: str = CHECK_REPORT_PATH
) -> None:
    safe_mkdir(REPORTS_PATH)
    with open(report_path, 'w') as report_file:
        json.dump(new_report, report_file, indent=4)


def merge_reports(
    old_report: List[Dict],
    new_report: List[Dict],
) -> List[Dict]:
    return list(dedup(
        itertools.chain(
            new_report,
            old_report
        ),
        key=lambda r: r['name']
    ))


class BaseChecker:
    def _ok(
        self,
        name: str,
        info: Optional[Union[str, Dict]] = None
    ) -> CheckResult:
        return CheckResult(name=name, status='ok', info=info)

    def _failed(
        self,
        name: str,
        info: Optional[Union[str, Dict]] = None
    ) -> CheckResult:
        return CheckResult(name=name, status='failed', info=info)

    def get_checks(self, check_type: CheckType = CheckType.ALL) -> FuncList:
        allowed_types = [check_type]

        if check_type == CheckType.ALL:
            allowed_types = [CheckType.PREINSTALL, CheckType.POSTINSTALL]

        methods = inspect.getmembers(
            type(self),
            predicate=lambda m: inspect.isfunction(m) and
            getattr(m, '_check_type', None) in allowed_types
        )
        return [functools.partial(m[1], self) for m in methods]

    def preinstall_check(self) -> ResultList:
        check_methods = self.get_checks(check_type=CheckType.PREINSTALL)
        return [cm() for cm in check_methods]

    def postinstall_check(self) -> ResultList:
        check_methods = self.get_checks(check_type=CheckType.POSTINSTALL)
        return [cm() for cm in check_methods]

    def check(self) -> ResultList:
        check_methods = self.get_checks()
        return [cm() for cm in check_methods]


class MachineChecker(BaseChecker):
    def __init__(
            self,
            requirements: Dict,
            disk_device: str,
            network_timeout: Optional[int] = None) -> None:
        self.requirements = requirements
        self.disk_device = disk_device
        self.network_timeout = network_timeout or NETWORK_CHECK_TIMEOUT

    @preinstall
    def cpu_total(self) -> CheckResult:
        name = 'cpu-total'
        actual = psutil.cpu_count(logical=True)
        expected = self.requirements['cpu_total']
        info = f'Expected {expected} logical cores, actual {actual} cores'
        if actual < expected:
            return self._failed(name=name, info=info)
        else:
            return self._ok(name=name, info=info)

    @preinstall
    def cpu_physical(self) -> CheckResult:
        name = 'cpu-physical'
        actual = psutil.cpu_count(logical=False)
        expected = self.requirements['cpu_physical']
        info = f'Expected {expected} physical cores, actual {actual} cores'
        if actual < expected:
            return self._failed(name=name, info=info)
        else:
            return self._ok(name=name, info=info)

    @preinstall
    def memory(self) -> CheckResult:
        name = 'memory'
        mem_info = psutil.virtual_memory().total,
        actual = mem_info[0]
        expected = self.requirements['memory']
        actual_gb = round(actual / 1024 ** 3, 2)
        expected_gb = round(expected / 1024 ** 3, 2)
        info = f'Expected RAM {expected_gb} GB, actual {actual_gb} GB'
        if actual < expected:
            return self._failed(name=name, info=info)
        else:
            return self._ok(name=name, info=info)

    @preinstall
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

    def _get_disk_size(self) -> int:
        return get_disk_size(self.disk_device)

    @preinstall
    def disk(self) -> CheckResult:
        name = 'disk'
        actual = self._get_disk_size()
        expected = self.requirements['disk']
        actual_gb = round(actual / 1024 ** 3, 2)
        expected_gb = round(expected / 1024 ** 3, 2)
        info = f'Expected disk size {expected_gb} GB, actual {actual_gb} GB'
        if actual < expected:
            return self._failed(name=name, info=info)
        else:
            return self._ok(name=name, info=info)

    @preinstall
    def network(self) -> CheckResult:
        name = 'network'
        try:
            socket.setdefaulttimeout(self.network_timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(
                (CLOUDFLARE_DNS_HOST, CLOUDFLARE_DNS_HOST_PORT))
            return self._ok(name=name)
        except socket.error as err:
            info = f'Network checking returned error: {err}'
            return self._failed(name=name, info=info)


class PackageChecker(BaseChecker):
    def __init__(self, requirements: Dict) -> None:
        self.requirements = requirements

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

    @preinstall
    def iptables_persistent(self) -> CheckResult:
        return self._check_apt_package('iptables-persistent')

    @preinstall
    def lvm2(self) -> CheckResult:
        return self._check_apt_package('lvm2')

    @preinstall
    def btrfs_progs(self) -> CheckResult:
        return self._check_apt_package('btrfs-progs')

    @preinstall
    def lsof(self) -> CheckResult:
        return self._check_apt_package('lsof')

    @preinstall
    def psmisc(self) -> CheckResult:
        return self._check_apt_package('psmisc')

    def _version_from_dpkg_output(self, output: str) -> str:
        info_lines = map(lambda s: s.strip(), output.split('\n'))
        v_line = next(filter(
            lambda s: s.startswith('Version'),
            info_lines
        ))
        return v_line.split()[1]


class DockerChecker(BaseChecker):
    def __init__(self, requirements: Dict) -> None:
        self.docker_client = docker.from_env()
        self.requirements = requirements

    def _check_docker_command(self) -> Optional[str]:
        return shutil.which('docker')

    def _get_docker_version_info(self) -> Optional[Dict]:
        try:
            return self.docker_client.version()
        except Exception as err:
            logger.error(f'Request to docker api failed {err}')
            return None

    @preinstall
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
        logger.debug('Docker version info %s', version_info)
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

    @preinstall
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
        logger.debug('Docker version info %s', version_info)
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

    @preinstall
    def docker_compose(self) -> CheckResult:
        name = 'docker-compose'
        cmd = shutil.which('docker-compose')
        if cmd is None:
            info = 'No such command: "docker-compose"'
            return self._failed(name=name, info=info)

        v_cmd_result = run_cmd(
            ['docker-compose', '-v'],
            check_code=False,
            separate_stderr=True
        )
        output = v_cmd_result.stdout.decode('utf-8').rstrip()
        if v_cmd_result.returncode != 0:
            info = f'Checking docker-compose version failed with: {output}'
            return self._failed(name=name, info=output)

        actual_version = output.split(',')[0].split()[-1].strip()
        expected_version = self.requirements['docker-compose']

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
        actual_value = config.get('hosts', [])
        sactual, sexpected = set(actual_value), set(DOCKER_DAEMON_HOSTS)
        if sactual & sexpected != sexpected:
            missing = sorted(sexpected - sactual)
            info = f'Docker daemon hosts is misconfigured. Missing hosts: {missing}'  # noqa
            return False, info
        else:
            info = 'Hosts is properly configured'
            return True, info

    @postinstall
    def keeping_containers_alive(self) -> CheckResult:
        name = 'live-restore'
        config = self._get_docker_config()
        is_ok, info = self._check_docker_alive_option(config)
        if is_ok:
            return self._ok(name=name, info=info)
        else:
            return self._failed(name=name, info=info)

    @postinstall
    def hosts_config(self) -> CheckResult:
        name = 'docker-hosts'
        config = self._get_docker_config()
        is_ok, info = self._check_docker_hosts_option(config)
        if is_ok:
            return self._ok(name=name, info=info)
        else:
            return self._failed(name=name, info=info)


def get_checks(
    checkers: List[BaseChecker],
    check_type: CheckType = CheckType.ALL
) -> FuncList:
    return list(
        itertools.chain.from_iterable(
            (
                checker.get_checks(check_type=check_type)
                for checker in checkers
            )
        )
    )


def get_all_checkers(disk: str, requirements: Dict) -> List[BaseChecker]:
    return [
        MachineChecker(requirements['server'], disk),
        PackageChecker(requirements['package']),
        DockerChecker(requirements['docker'])
    ]


def run_checks(
    disk: str,
    env_type: str = 'mainnet',
    config_path: str = CONTAINER_CONFIG_PATH,
    check_type: CheckType = CheckType.ALL
) -> ResultList:
    logger.info('Executing checks. Type: %s', check_type)
    requirements = get_static_params(env_type, config_path)
    checkers = get_all_checkers(disk, requirements)
    checks = get_checks(checkers, check_type)
    results = [check() for check in checks]

    saved_report = get_report()
    report = generate_report_from_result(results)
    new_report = merge_reports(saved_report, report)
    save_report(new_report)

    failed = list(filter(lambda r: r.status != 'ok', results))
    if failed:
        logger.info('Host is not fully meet the requirements')
    return failed
