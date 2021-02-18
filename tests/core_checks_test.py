import time
from pip._internal import main as pipmain

import mock
import pytest

from core.checks import RequirementsChecker


@pytest.fixture
def requirements_data():
    return {
        'hardware': {
            'cpu_total': 1,
            'cpu_physical': 1,
            'memory': 100,
            'swap': 100
        },
        'packages': {
            'docker-compose': '1.27.4',
            'docker': None,
            'iptables_persistant': None,
            'lvm2': None
        }
    }


def test_requirements_cpu_total(requirements_data):
    checker = RequirementsChecker(requirements_data)
    assert checker.cpu_total().status == 'ok', checker.cpu_total()
    requirements_data['hardware']['cpu_total'] = 10000  # too big
    checker = RequirementsChecker(requirements_data)
    assert checker.cpu_total().status == 'error'


def test_requirements_cpu_physical(requirements_data):
    checker = RequirementsChecker(requirements_data)
    assert checker.cpu_physical().status == 'ok'
    requirements_data['hardware']['cpu_physical'] = 10000  # too big
    checker = RequirementsChecker(requirements_data)
    assert checker.cpu_physical().status == 'error'


def test_requirements_memory(requirements_data):
    checker = RequirementsChecker(requirements_data)
    assert checker.memory().status == 'ok'
    requirements_data['hardware']['memory'] = 10000000000000  # too big
    checker = RequirementsChecker(requirements_data)
    assert checker.memory().status == 'error'


def test_requirements_swap(requirements_data):
    checker = RequirementsChecker(requirements_data)
    assert checker.swap().status == 'ok'
    requirements_data['hardware']['swap'] = 10000000000000  # too big
    checker = RequirementsChecker(requirements_data)
    assert checker.swap().status == 'error'


def test_requirements_network():
    checker = RequirementsChecker({})
    assert checker.network().status == 'ok'


def test_requirements_docker_daemon():
    checker = RequirementsChecker({})
    res_mock = mock.Mock()
    res_mock.stdout = b'Test output'

    def run_cmd_mock(*args, **kwargs):
        return res_mock

    res_mock.returncode = 0
    with mock.patch('core.checks.run_cmd', run_cmd_mock):
        assert checker.docker().status == 'ok'
    res_mock.returncode = 1
    with mock.patch('core.checks.run_cmd', run_cmd_mock):
        assert checker.docker().status == 'error'


def test_requirements_iptables_persistent():
    checker = RequirementsChecker({})
    res_mock = mock.Mock()
    res_mock.stdout = b'Test output'

    def run_cmd_mock(*args, **kwargs):
        return res_mock

    res_mock.returncode = 0
    with mock.patch('core.checks.run_cmd', run_cmd_mock):
        assert checker.iptables_persistent().status == 'ok'
    res_mock.returncode = 1
    with mock.patch('core.checks.run_cmd', run_cmd_mock):
        assert checker.iptables_persistent().status == 'error'


def test_requirements_lvm2():
    checker = RequirementsChecker({})
    res_mock = mock.Mock()
    res_mock.stdout = b'Test output'

    def run_cmd_mock(*args, **kwargs):
        return res_mock

    res_mock.returncode = 0
    with mock.patch('core.checks.run_cmd', run_cmd_mock):
        assert checker.lvm2().status == 'ok'
    res_mock.returncode = 1
    with mock.patch('core.checks.run_cmd', run_cmd_mock):
        assert checker.lvm2().status == 'error'


@pytest.fixture
def docker_compose_pkg_1_27_4():
    pipmain(['install', 'docker-compose==1.27.4'])
    time.sleep(2)
    yield
    pipmain(['uninstall', 'docker-compose', '-y'])


@pytest.fixture
def docker_compose_pkg_1_24_1():
    pipmain(['install', 'docker-compose==1.24.1'])
    time.sleep(2)
    yield
    pipmain(['uninstall', 'docker-compose', '-y'])


def test_requirements_docker_compose(
        requirements_data, docker_compose_pkg_1_27_4):
    checker = RequirementsChecker(requirements_data)
    cr = checker.docker_compose().status == 'ok'
    print(cr)
    assert checker.docker_compose().status == 'ok'


def test_requirements_docker_compose_no_pkg(
        requirements_data):
    checker = RequirementsChecker(requirements_data)
    assert checker.docker_compose().status == 'error'


def test_requirements_docker_compose_invalid_version(
        requirements_data, docker_compose_pkg_1_24_1):
    checker = RequirementsChecker(requirements_data)
    assert checker.docker_compose().status == 'error'


def test_requirements_docker_service_status():
    checker = RequirementsChecker({})
    checker.docker_client = mock.Mock()
    assert checker.docker_service_status().status == 'ok'


def test_requirements_docker_config():
    checker = RequirementsChecker({})
    valid_config = {
        'live-restore': True
    }
    assert checker.check_docker_alive_option(valid_config).status == 'ok'
    invalid_config = {
        'live-restore': False
    }
    r = checker.check_docker_alive_option(invalid_config)
    assert r.status == 'error'
    assert r.info == {'actual_value': False, 'expected_value': True}

    r = checker.check_docker_alive_option({})
    assert r.status == 'error'
    assert r.info == {'actual_value': None, 'expected_value': True}
