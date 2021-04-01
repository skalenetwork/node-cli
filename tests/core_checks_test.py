import time
from pip._internal import main as pipmain

import mock
import pytest

from node_cli.core.checks import DockerChecker, MachineChecker, PackagesChecker


@pytest.fixture
def requirements_data():
    return {
        'server': {
            'cpu_total': 1,
            'cpu_physical': 1,
            'memory': 100,
            'swap': 100
        },
        'packages': {
            'docker-compose': '1.27.4',
            'iptables_persistant': '0.0.0',
            'lvm2': '0.0.0',
            'test-package': '2.2.2'
        },
        'docker': {
            'docker-engine': '0.0.0',
            'docker-api': '0.0.0',
        }
    }


def test_checks_cpu_total(requirements_data):
    checker = MachineChecker(requirements_data)
    r = checker.cpu_total()
    assert r.name == 'cpu-total'
    assert r.status == 'ok'
    requirements_data['server']['cpu_total'] = 10000  # too big
    checker = MachineChecker(requirements_data)
    r = checker.cpu_total()
    assert r.name == 'cpu-total'
    assert r.status == 'error'
    assert checker.cpu_total().status == 'error'


def test_checks_cpu_physical(requirements_data):
    checker = MachineChecker(requirements_data)
    r = checker.cpu_physical()
    assert r.name == 'cpu-physical'
    assert r.status == 'ok'
    requirements_data['server']['cpu_physical'] = 10000  # too big
    checker = MachineChecker(requirements_data)
    r = checker.cpu_physical()
    assert r.name == 'cpu-physical'
    assert r.status == 'error'


def test_checks_memory(requirements_data):
    checker = MachineChecker(requirements_data)
    r = checker.memory()
    assert r.name == 'memory'
    assert r.status == 'ok'
    # too big
    requirements_data['server']['memory'] = 10000000000000
    checker = MachineChecker(requirements_data)
    r = checker.memory()
    assert r.name == 'memory'
    assert r.status == 'error'


def test_checks_machine_check(requirements_data):
    checker = MachineChecker(requirements_data)
    result = checker.check()
    assert any([r.status == 'ok' for r in result])


def test_checks_swap(requirements_data):
    checker = MachineChecker(requirements_data)
    r = checker.swap()
    assert r.name == 'swap'
    assert r.status == 'ok'
    # too big
    requirements_data['server']['swap'] = 10000000000000
    checker = MachineChecker(requirements_data)
    r = checker.swap()
    assert r.name == 'swap'
    assert r.status == 'error'


def test_checks_network(requirements_data):
    checker = MachineChecker(requirements_data)
    r = checker.network()
    assert r.status == 'ok'
    assert r.name == 'network'


def test_checks_docker_engine(requirements_data):
    checker = DockerChecker(requirements_data)

    r = checker.docker_engine()
    assert r.name == 'docker-engine'
    assert r.status == 'ok'

    with mock.patch('shutil.which', return_value=None):
        r = checker.docker_engine()
        assert r.name == 'docker-engine'
        assert r.status == 'error'
        assert r.info == 'No such command: "docker"'

    requirements_data['docker']['docker-engine'] = '111.111.111'
    r = checker.docker_engine()
    assert r.name == 'docker-engine'
    assert r.status == 'error'
    assert r.info['expected_version'] == '111.111.111'


def test_checks_docker_api(requirements_data):
    checker = DockerChecker(requirements_data)

    r = checker.docker_api()
    assert r.name == 'docker-api'
    assert r.status == 'ok'

    with mock.patch('shutil.which', return_value=None):
        r = checker.docker_api()
        assert r.name == 'docker-api'
        assert r.status == 'error'
        assert r.info == 'No such command: "docker"'

    requirements_data['docker']['docker-api'] = '111.111.111'
    r = checker.docker_api()
    assert r.name == 'docker-api'
    assert r.status == 'error'
    assert r.info['expected_version'] == '111.111.111'


def test_checks_apt_package(requirements_data):
    checker = PackagesChecker(requirements_data)
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
        assert r.status == 'error'

    res_mock.stdout = b"""Package: test-package
        Version: 2.2.2
    """
    with mock.patch('node_cli.core.checks.run_cmd', run_cmd_mock):
        r = checker._check_apt_package(apt_package_name)
        assert r.name == 'test-package'
        assert r.status == 'ok'


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


def test_checks_docker_compose_valid_pkg(
        requirements_data, docker_compose_pkg_1_27_4):
    checker = PackagesChecker(requirements_data)
    print('Debug: ', checker.docker_compose())

    r = checker.docker_compose()
    r.name == 'docker-compose'
    r.status == 'ok'


def test_checks_docker_compose_no_pkg(
        requirements_data):
    checker = PackagesChecker(requirements_data)
    r = checker.docker_compose()
    r.name == 'docker-compose'
    r.status == 'ok'


def test_checks_docker_compose_invalid_version(
        requirements_data, docker_compose_pkg_1_24_1):
    checker = PackagesChecker(requirements_data)
    r = checker.docker_compose()
    r.name == 'docker-compose'
    r.status == 'ok'


def test_checks_docker_config():
    checker = DockerChecker(requirements_data)
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
