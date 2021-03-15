import os
import mock
import pytest

from node_cli.utils.validations import (
    read_g_config, generate_g_config_file, safe_get_user, is_user_valid, get_g_conf_user,
    check_not_inited, check_inited, check_user
)
from node_cli.utils.helper import write_json


TEST_GLOBAL_SKALE_DIR = os.path.join(os.environ.get('HOME_DIR'), 'etc', 'skale')
TEST_G_CONF_FP = os.path.join(TEST_GLOBAL_SKALE_DIR, 'conf.json')


def test_read_g_config():
    write_json(TEST_G_CONF_FP, {'test': 1})
    with mock.patch('node_cli.utils.validations.GLOBAL_SKALE_CONF_FILEPATH', new=TEST_G_CONF_FP), \
            mock.patch('node_cli.utils.validations.GLOBAL_SKALE_DIR', new=TEST_GLOBAL_SKALE_DIR):
        g_config = read_g_config()
    assert g_config['test'] == 1


def test_generate_g_config_file():
    try:
        os.remove(TEST_G_CONF_FP)
    except OSError:
        pass

    assert not os.path.exists(TEST_G_CONF_FP)
    with mock.patch('node_cli.utils.validations.GLOBAL_SKALE_CONF_FILEPATH', new=TEST_G_CONF_FP), \
            mock.patch('node_cli.utils.validations.GLOBAL_SKALE_DIR', new=TEST_GLOBAL_SKALE_DIR):
        generate_g_config_file()
    assert os.path.exists(TEST_G_CONF_FP)

    g_config = read_g_config()
    assert g_config['user'] == safe_get_user()
    assert g_config['home_dir'] == os.path.expanduser('~')


def test_safe_get_user():
    sudo_user = os.environ.get('SUDO_USER')
    if sudo_user:
        del os.environ['SUDO_USER']
    os.environ['USER'] = 'test'
    assert safe_get_user() == 'test'
    if sudo_user:
        os.environ['SUDO_USER'] = sudo_user


def test_is_user_valid():
    with mock.patch('node_cli.utils.validations.GLOBAL_SKALE_CONF_FILEPATH', new=TEST_G_CONF_FP):
        generate_g_config_file()
        assert is_user_valid()

        write_json(TEST_G_CONF_FP, {'user': 'skaletest'})
        assert not is_user_valid()

        sudo_user = os.environ.get('SUDO_USER')
        os.environ['SUDO_USER'] = 'root'
        assert is_user_valid()
        assert not is_user_valid(allow_root=False)

        if sudo_user:
            os.environ['SUDO_USER'] = sudo_user
        else:
            del os.environ['SUDO_USER']


def test_get_g_conf_user():
    write_json(TEST_G_CONF_FP, {'user': 'test_get_g_conf_user'})
    with mock.patch('node_cli.utils.validations.GLOBAL_SKALE_CONF_FILEPATH', new=TEST_G_CONF_FP):
        assert get_g_conf_user() == 'test_get_g_conf_user'


def test_check_not_inited():
    @check_not_inited
    def requires_not_inited_node():
        pass
    with mock.patch('node_cli.utils.validations.is_node_inited', return_value=False):
        requires_not_inited_node()
    with mock.patch('node_cli.utils.validations.is_node_inited', return_value=True):
        with pytest.raises(SystemExit):
            requires_not_inited_node()


def test_check_inited():
    @check_inited
    def requires_inited_node():
        pass
    with mock.patch('node_cli.utils.validations.is_node_inited', return_value=True):
        requires_inited_node()
    with mock.patch('node_cli.utils.validations.is_node_inited', return_value=False):
        with pytest.raises(SystemExit):
            requires_inited_node()


def test_check_user():
    @check_user
    def this_checks_user():
        pass
    with mock.patch('node_cli.utils.validations.GLOBAL_SKALE_CONF_FILEPATH', new=TEST_G_CONF_FP):
        generate_g_config_file()
        this_checks_user()
        write_json(TEST_G_CONF_FP, {'user': 'skaletest'})
        with pytest.raises(SystemExit):
            this_checks_user()
