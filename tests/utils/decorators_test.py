import mock
import pytest

from node_cli.utils.global_config import generate_g_config_file
from node_cli.utils.decorators import check_not_inited, check_inited, check_user
from node_cli.utils.helper import write_json

from tests.conftest import TEST_G_CONF_FP


def test_check_not_inited():
    @check_not_inited
    def requires_not_inited_node():
        pass
    with mock.patch('node_cli.utils.decorators.is_node_inited', return_value=False):
        requires_not_inited_node()
    with mock.patch('node_cli.utils.decorators.is_node_inited', return_value=True):
        with pytest.raises(SystemExit):
            requires_not_inited_node()


def test_check_inited():
    @check_inited
    def requires_inited_node():
        pass
    with mock.patch('node_cli.utils.decorators.is_node_inited', return_value=True):
        requires_inited_node()
    with mock.patch('node_cli.utils.decorators.is_node_inited', return_value=False):
        with pytest.raises(SystemExit):
            requires_inited_node()


def test_check_user(mocked_g_config):
    @check_user
    def this_checks_user():
        pass
    generate_g_config_file()
    this_checks_user()
    write_json(TEST_G_CONF_FP, {'user': 'skaletest'})
    with pytest.raises(SystemExit):
        this_checks_user()
