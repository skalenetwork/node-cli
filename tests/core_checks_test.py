import os
import shutil
import time
from pip._internal import main as pipmain

import mock
import pytest

from node_cli.configs import STATIC_PARAMS_FILEPATH

from node_cli.core.checks import (
    CheckType,
    DockerChecker,
    generate_report_from_result,
    get_all_checkers,
    get_checks,
    get_report,
    get_static_params,
    MachineChecker,
    merge_reports,
    PackageChecker,
    save_report
)


@pytest.fixture
def requirements_data():
    return {
        'server': {
            'cpu_total': 1,
            'cpu_physical': 1,
            'memory': 100,
            'swap': 100,
            'disk': 100000000
        },
        'package': {
            'iptables_persistant': '0.0.0',
            'lvm2': '0.0.0',
            'test-package': '2.2.2'
        },
        'docker': {
            'docker-engine': '0.0.0',
            'docker-api': '0.0.0',
            'docker-compose': '1.27.4'
        }
    }


@pytest.fixture
def server_req(requirements_data):
    return requirements_data['server']


def test_checks_errored():
    checker = MachineChecker({}, 'test-disk')
    r = checker.check()
    for c in r:
        if c.name != 'network' and c.name != 'disk':
            assert c.status == 'error', c.name
            assert c.info.startswith('KeyError'), c.name


def test_checks_cpu_total(server_req):
    checker = MachineChecker(server_req, 'test-disk')
    r = checker.cpu_total()
    assert r.name == 'cpu-total'
    assert r.status == 'ok'
    server_req['cpu_total'] = 10000  # too big
    checker = MachineChecker(server_req, 'test-disk')
    r = checker.cpu_total()
    assert r.name == 'cpu-total'
    assert r.status == 'failed'
    assert checker.cpu_total().status == 'failed'


def test_checks_cpu_physical(server_req):
    checker = MachineChecker(server_req, 'test-disk')
    r = checker.cpu_physical()
    assert r.name == 'cpu-physical'
    assert r.status == 'ok'
    server_req['cpu_physical'] = 10000  # too big
    checker = MachineChecker(server_req, 'test-disk')
    r = checker.cpu_physical()
    assert r.name == 'cpu-physical'
    assert r.status == 'failed'


def test_checks_memory(server_req):
    checker = MachineChecker(server_req, 'test-disk')
    r = checker.memory()
    assert r.name == 'memory'
    assert r.status == 'ok'
    # too big
    server_req['memory'] = 10000000000000
    checker = MachineChecker(server_req, 'test-disk')
    r = checker.memory()
    assert r.name == 'memory'
    assert r.status == 'failed'


def test_checks_swap(server_req):
    checker = MachineChecker(server_req, 'test-disk')
    r = checker.swap()
    assert r.name == 'swap'
    assert r.status == 'ok'
    # too big
    server_req['swap'] = 10000000000000
    checker = MachineChecker(server_req, 'test-disk')
    r = checker.swap()
    assert r.name == 'swap'
    assert r.status == 'failed'


def test_checks_network(server_req):
    checker = MachineChecker(server_req, 'test-disk', network_timeout=10)
    r = checker.network()
    assert r.status == 'ok', r.info
    assert r.name == 'network'


def test_checks_disk(server_req):
    checker = MachineChecker(server_req, 'test-disk')
    r = checker.disk()
    assert r.status == 'error'
    assert r.name == 'disk'

    checker = MachineChecker(server_req, 'test-disk')
    checker._get_disk_size = mock.Mock(return_value=float('inf'))
    r = checker.disk()
    assert r.status == 'ok'
    assert r.name == 'disk'

    checker = MachineChecker(server_req, 'test-disk')
    checker._get_disk_size = mock.Mock(return_value=50)
    r = checker.disk()
    assert r.status == 'failed'
    assert r.name == 'disk'
    assert r.info == 'Expected disk size 0.09 GB, actual 0.0 GB'


def test_checks_machine_check(server_req):
    checker = MachineChecker(server_req, 'test-disk', network_timeout=10)
    result = checker.check()
    assert not all([r.status == 'ok' for r in result])

    checker = MachineChecker(server_req, 'test-disk')
    checker._get_disk_size = mock.Mock(return_value=float('inf'))
    result = checker.check()
    assert all([r.status == 'ok' for r in result])
    report = generate_report_from_result(result)
    assert report == [
        {'name': 'cpu-physical', 'status': 'ok'},
        {'name': 'cpu-total', 'status': 'ok'},
        {'name': 'disk', 'status': 'ok'},
        {'name': 'memory', 'status': 'ok'},
        {'name': 'network', 'status': 'ok'},
        {'name': 'swap', 'status': 'ok'}
    ]


@pytest.fixture
def docker_req(requirements_data):
    return requirements_data['docker']


def test_checks_docker_engine(docker_req):
    checker = DockerChecker(docker_req)

    r = checker.docker_engine()
    assert r.name == 'docker-engine'
    assert r.status == 'ok'

    with mock.patch('shutil.which', return_value=None):
        r = checker.docker_engine()
        assert r.name == 'docker-engine'
        assert r.status == 'failed'
        assert r.info == 'No such command: "docker"'

    docker_req['docker-engine'] = '111.111.111'
    r = checker.docker_engine()
    assert r.name == 'docker-engine'
    assert r.status == 'failed'
    assert r.info['expected_version'] == '111.111.111'


def test_checks_docker_api(docker_req):
    checker = DockerChecker(docker_req)

    r = checker.docker_api()
    assert r.name == 'docker-api'
    assert r.status == 'ok'

    with mock.patch('shutil.which', return_value=None):
        r = checker.docker_api()
        assert r.name == 'docker-api'
        assert r.status == 'failed'
        assert r.info == 'No such command: "docker"'

    docker_req['docker-api'] = '111.111.111'
    r = checker.docker_api()
    assert r.name == 'docker-api'
    assert r.status == 'failed'
    assert r.info['expected_version'] == '111.111.111'


@pytest.fixture
def docker_compose_pkg_1_27_4():
    pipmain(['install', 'docker-compose==1.27.4'])
    time.sleep(10)
    yield
    pipmain(['uninstall', 'docker-compose', '-y'])


@pytest.fixture
def docker_compose_pkg_1_24_1():
    pipmain(['install', 'docker-compose==1.24.1'])
    time.sleep(10)
    yield
    pipmain(['uninstall', 'docker-compose', '-y'])


def test_checks_docker_compose_good_pkg(docker_req, docker_compose_pkg_1_27_4):
    checker = DockerChecker(package_req)
    r = checker.docker_compose()
    r.name == 'docker-compose'
    r.status == 'ok'


def test_checks_docker_compose_no_pkg(docker_req):
    checker = DockerChecker(package_req)
    r = checker.docker_compose()
    r.name == 'docker-compose'
    r.status == 'ok'


def test_checks_docker_compose_invalid_version(
    docker_req,
    docker_compose_pkg_1_24_1
):
    checker = DockerChecker(docker_req)
    r = checker.docker_compose()
    r.name == 'docker-compose'
    r.status == 'ok'


def test_checks_docker_config(docker_req):
    checker = DockerChecker(docker_req)
    valid_config = {
        'live-restore': True
    }
    r = checker._check_docker_alive_option(valid_config)
    assert r[0] is True
    assert r[1] == 'Docker daemon live-restore option is set as "true"'

    invalid_config = {
        'live-restore': False
    }
    r = checker._check_docker_alive_option(invalid_config)
    assert r[0] is False
    assert r[1] == 'Docker daemon live-restore option should be set as "true"'

    r = checker._check_docker_alive_option({})
    assert r[0] is False
    assert r[1] == 'Docker daemon live-restore option should be set as "true"'


def test_checks_docker_hosts(docker_req):
    checker = DockerChecker(docker_req)
    valid_config = {'hosts': ['unix:///var/run/skale/docker.sock', 'fd://']}
    r = checker._check_docker_hosts_option(valid_config)
    assert r == (True, 'Hosts is properly configured')

    invalid_config = {'hosts': []}
    r = checker._check_docker_hosts_option(invalid_config)
    assert r == (
        False,
        "Docker daemon hosts is misconfigured. Missing hosts: ['fd://', 'unix:///var/run/skale/docker.sock']"  # noqa
    )

    invalid_config = {'hosts': ['http://127.0.0.1:8080']}
    r = checker._check_docker_hosts_option(invalid_config)
    assert r == (False, "Docker daemon hosts is misconfigured. Missing hosts: ['fd://', 'unix:///var/run/skale/docker.sock']")  # noqa

    invalid_config = {'hosts': ['fd://']}
    r = checker._check_docker_hosts_option(invalid_config)
    assert r == (False, "Docker daemon hosts is misconfigured. Missing hosts: ['unix:///var/run/skale/docker.sock']")  # noqa


def test_checks_docker_pre_post_install_checks(docker_req):
    checker = DockerChecker(docker_req)
    result = checker.preinstall_check()
    assert len(result) == 3
    result = checker.postinstall_check()
    assert len(result) == 2


@pytest.fixture
def package_req(requirements_data):
    return requirements_data['package']


def test_checks_apt_package(package_req):
    checker = PackageChecker(package_req)
    res_mock = mock.Mock()
    res_mock.stdout = b"""Package: test-package
        Version: 5.2.1-2
    """

    def run_cmd_mock(*args, **kwargs):
        return res_mock

    res_mock.returncode = 0
    apt_package_name = 'test-package'
    with mock.patch('node_cli.core.checks.run_cmd', run_cmd_mock):
        r = checker._check_apt_package(apt_package_name)
        assert r.name == apt_package_name
        assert r.status == 'ok'

    res_mock.stdout = b"""Package: test-package
        Version: 1.1.1
    """
    with mock.patch('node_cli.core.checks.run_cmd', run_cmd_mock):
        r = checker._check_apt_package(apt_package_name)
        assert r.name == 'test-package'
        assert r.status == 'failed'

    res_mock.stdout = b"""Package: test-package
        Version: 2.2.2
    """
    with mock.patch('node_cli.core.checks.run_cmd', run_cmd_mock):
        r = checker._check_apt_package(apt_package_name)
        assert r.name == 'test-package'
        assert r.status == 'ok'


def test_get_all_checkers(requirements_data):
    disk = 'test-disk'
    checkers = get_all_checkers(disk, requirements_data)
    assert len(checkers) == 3
    assert isinstance(checkers[0], MachineChecker)
    assert isinstance(checkers[1], PackageChecker)
    assert isinstance(checkers[2], DockerChecker)


def test_get_checks(requirements_data):
    disk = 'test-disk'
    checkers = get_all_checkers(disk, requirements_data)
    checks = get_checks(checkers)
    assert len(checks) == 16
    checks = get_checks(checkers, check_type=CheckType.PREINSTALL)
    assert len(checks) == 14
    checks = get_checks(checkers, check_type=CheckType.POSTINSTALL)
    assert len(checks) == 2


def test_get_save_report(tmp_dir_path):
    path = os.path.join(tmp_dir_path, 'checks.json')
    report = get_report(path)
    assert report == []
    report.append({'name': 'test', 'status': 'ok', 'info': 'Test'})
    save_report(report, path)
    saved_report = get_report(path)
    assert saved_report == report


def test_merge_report():
    old_report = [
        {'name': 'test1', 'status': 'ok', 'info': 'Test'},
        {'name': 'test2', 'status': 'failed', 'info': 'Test1'},
        {'name': 'test3', 'status': 'failed', 'info': 'Test1'}
    ]
    new_report = [
        {'name': 'test1', 'status': 'ok', 'info': 'Test'},
        {'name': 'test2', 'status': 'ok', 'info': 'Test1'}
    ]
    report = merge_reports(old_report, new_report)
    assert report == [
        {'name': 'test1', 'status': 'ok', 'info': 'Test'},
        {'name': 'test2', 'status': 'ok', 'info': 'Test1'},
        {'name': 'test3', 'status': 'failed', 'info': 'Test1'}
    ]


def test_get_static_params(tmp_config_dir):
    params = get_static_params()
    shutil.copy(STATIC_PARAMS_FILEPATH, tmp_config_dir)
    tmp_params = get_static_params(config_path=tmp_config_dir)
    assert params['server']['cpu_total'] == 8
    assert params == tmp_params
