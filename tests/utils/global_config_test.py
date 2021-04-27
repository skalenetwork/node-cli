
import os
import mock
from node_cli.utils.global_config import read_g_config, generate_g_config_file
from node_cli.utils.helper import write_json, get_system_user, is_user_valid, get_g_conf_user
from node_cli.configs import GLOBAL_SKALE_DIR, GLOBAL_SKALE_CONF_FILEPATH


def test_read_g_config(mocked_g_config):
    write_json(GLOBAL_SKALE_CONF_FILEPATH, {'test': 1})
    g_config = read_g_config(GLOBAL_SKALE_DIR, GLOBAL_SKALE_CONF_FILEPATH)
    assert g_config['test'] == 1


def test_generate_g_config_file(mocked_g_config):
    try:
        os.remove(GLOBAL_SKALE_CONF_FILEPATH)
    except OSError:
        pass

    assert not os.path.exists(GLOBAL_SKALE_CONF_FILEPATH)
    generate_g_config_file(GLOBAL_SKALE_DIR, GLOBAL_SKALE_CONF_FILEPATH)
    assert os.path.exists(GLOBAL_SKALE_CONF_FILEPATH)

    g_config = read_g_config(GLOBAL_SKALE_DIR, GLOBAL_SKALE_CONF_FILEPATH)
    assert g_config['user'] == get_system_user()
    assert g_config['home_dir'] == os.path.expanduser('~')


def test_get_system_user():
    sudo_user = os.environ.get('SUDO_USER')
    if sudo_user:
        del os.environ['SUDO_USER']
    os.environ['USER'] = 'test'
    assert get_system_user() == 'test'
    if sudo_user:
        os.environ['SUDO_USER'] = sudo_user


def test_is_user_valid(mocked_g_config):
    generate_g_config_file(GLOBAL_SKALE_DIR, GLOBAL_SKALE_CONF_FILEPATH)
    assert is_user_valid()

    write_json(GLOBAL_SKALE_CONF_FILEPATH, {'user': 'skaletest'})
    assert not is_user_valid()

    with mock.patch('os.getuid', return_value=0):
        assert is_user_valid()
        assert not is_user_valid(allow_root=False)


def test_get_g_conf_user(mocked_g_config):
    write_json(GLOBAL_SKALE_CONF_FILEPATH, {'user': 'test_get_g_conf_user'})
    assert get_g_conf_user() == 'test_get_g_conf_user'
