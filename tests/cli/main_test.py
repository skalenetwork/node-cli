import mock
import pytest
import requests

import cli.info as info

from mock import MagicMock, Mock
from main import (user, version, attach, host, user_token,
                  register, login, wallet)
from tests.helper import run_command, run_command_mock
import main


@pytest.fixture
def config():
    config_mock = {
        'host': 'https://test.com',
        'cookies': {'cookie_key': 'cookie_value'}
    }
    with mock.patch('tools.helper.session_config',
                    MagicMock(return_value=config_mock)):
        yield


@pytest.fixture
def skip_auth(monkeypatch):
    monkeypatch.setattr('core.helper.cookies_exists', Mock(return_value=True))


def test_version(config):
    result = run_command(version, [])
    expected = f'SKALE Node CLI version: {info.VERSION}\n'
    assert result.output == expected
    result = run_command(version, ['--short'])
    assert result.output == f'{info.VERSION}\n'


def test_attach():
    result = run_command(attach)
    assert result.exit_code == 2
    expected =  'Usage: attach [OPTIONS] HOST\nTry "attach --help" for help.\n\nError: Missing argument "HOST".\n'  # noqa
    assert result.output == expected

    result = run_command(attach, ['darova'])
    assert result.exit_code == 0
    assert result.output == 'Provided SKALE node host is not valid\n'

    result = run_command(attach, ['http://127.0.0.1', '--skip-check'])
    assert result.output == 'SKALE host: http://127.0.0.1:3007\n'


def test_host():
    result = run_command(host, [])
    assert result.output == 'SKALE node host: http://127.0.0.1:3007\n'
    result = run_command(host, ['--reset'])
    assert result.output == 'Host removed, cookies cleaned.\n'


def test_user_token(config):
    test_token = '231test-token'
    with mock.patch('core.user.get_registration_token_data',
                    new=MagicMock(return_value={'token': test_token})):
        result = run_command(user_token, [])
        assert result.output == f'User registration token: {test_token}\n'
        result = run_command(user_token, ['--short'])
        assert result.output == '231test-token\n'

    with mock.patch('core.user.get_registration_token_data',
                    new=MagicMock(return_value=None)):
        result = run_command(user_token, [])
        assert result.exit_code == 0
        print(result.output)
        assert result.output == ("Couldn't find registration tokens file. "
                                 "Check that node inited on this machine.\n")


def test_register(config):
    response_mock = MagicMock()
    response_mock.status_code = requests.codes.ok
    response_mock.cookies = 'cookies'
    result = run_command_mock('core.user.post_request',
                              response_mock,
                              register,
                              input="test\n qwerty1\n token")
    expected = (
        'Enter username: test\n'
        'Enter password: \n'
        'Enter one-time token: \n'
        'User created: test\n'
        'Success, cookies saved.\n'
    )
    assert result.exit_code == 0
    assert result.output == expected

    response_mock.status_code = -1
    response_mock.text = '{"errors": [{"msg": "Token not match"}]}'
    result = run_command_mock('core.user.post_request',
                              response_mock,
                              register,
                              input="test\n qwerty1\n token")
    assert result.exit_code == 0
    expected = (
        'Enter username: test\n'
        'Enter password: \n'
        'Enter one-time token: \n'
        'Registration failed: {"errors": [{"msg": "Token not match"}]}\n'
    )
    assert expected == result.output


def test_login(config):
    response_mock = MagicMock()
    response_mock.status_code = requests.codes.ok
    response_mock.cookies = 'simple-cookies'
    result = run_command_mock('core.user.post_request',
                              response_mock,
                              login,
                              input="test\n qwerty1\n token")
    expected = (
        'Enter username: test\n'
        'Enter password: \n'
        'Success, cookies saved.\n'
    )
    assert result.exit_code == 0
    assert result.output == expected

    response_mock.status_code = -1
    response_mock.text = '{"errors": [{"msg": "Test error"}]}'
    result = run_command_mock('core.user.post_request',
                              response_mock,
                              login,
                              input="test\n qwerty1")
    assert result.exit_code == 0
    expected = (
        'Enter username: test\n'
        'Enter password: \n'
        'Authorization failed: {"errors": [{"msg": "Test error"}]}\n'
    )
    print(result.output)
    assert expected == result.output


def test_logout():
    response_mock = MagicMock()
    response_mock.status_code = requests.codes.ok
    response_mock.cookies = 'simple-cookies'
    result = run_command_mock('core.user.get_request',
                              response_mock,
                              user,
                              ['logout'],
                              input="test\n qwerty1\n token")
    assert result.exit_code == 0
    expected = 'Cookies removed\n'
    assert result.output == expected

    response_mock.status_code = -1
    response_mock.text = '{"errors": [{"msg": "Test error"}]}'
    result = run_command_mock('core.user.get_request',
                              response_mock,
                              user,
                              ['logout'],
                              input="test\n qwerty1")
    assert result.exit_code == 0
    expected = (
        'Logout failed:\n'
        '{"errors": [{"msg": "Test error"}]}\n'
    )
    assert expected == result.output


def test_wallet_info(skip_auth, config):
    response_mock = MagicMock({'host': 'test.com'})
    response_mock.status_code = requests.codes.ok
    response_mock.json = Mock(return_value={'data': 'wallet_data'})
    result = run_command_mock('core.user.get_request',
                              response_mock,
                              main.wallet,
                              ['info'])
    assert result.exit_code == 0
    expected = 'Cookies removed\n'
    print(result.output)
    assert result.output == expected
