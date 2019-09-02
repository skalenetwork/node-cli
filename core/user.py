import requests
import logging
import pickle
import json
from core.config import URLS, TOKENS_FILEPATH
from core.helper import safe_get_config, construct_url, clean_cookies, get_localhost_endpoint, \
    get_request, post_request

logger = logging.getLogger(__name__)


def register_user(config, username, password, token):
    host = safe_get_config(config, 'host')
    if not host:
        host = get_localhost_endpoint()
    data = {
        'username': username,
        'password': password,
        'token': token
    }
    url = construct_url(host, URLS['register'])
    response = post_request(url, data)
    if response is None:
        return None

    if response.status_code == requests.codes.ok:
        cookies_text = pickle.dumps(response.cookies)
        config['cookies'] = cookies_text
        print(f'User created: {username}')
        print('Success, cookies saved.')
    else:
        print('Registration failed: ' + response.text)


def login_user(config, username, password):
    host = safe_get_config(config, 'host')
    if not host:
        host = get_localhost_endpoint()

    data = {
        'username': username,
        'password': password
    }
    url = construct_url(host, URLS['login'])
    response = post_request(url, data)
    if response is None:
        return None

    if response.status_code == requests.codes.ok:
        cookies_text = pickle.dumps(response.cookies)
        config['cookies'] = cookies_text
        print('Success, cookies saved.')
    else:
        print('Authorization failed: ' + response.text)


def logout_user(config):
    host = safe_get_config(config, 'host')
    url = construct_url(host, URLS['logout'])
    response = get_request(url)
    if response is None:
        return None

    if response.status_code == requests.codes.ok:
        clean_cookies(config)
        print('Cookies removed')
    else:
        print('Logout failed')
        print(response.text)


def show_registration_token(short):
    try:
        with open(TOKENS_FILEPATH, encoding='utf-8') as data_file:
            config = json.loads(data_file.read())
        if short:
            print(config["token"])
        else:
            print(f'User registration token: {config["token"]}')
    except FileNotFoundError as e:
        err_msg = "Couldn't find registration tokens file. Check that node inited on this machine."
        logger.error(err_msg)
        print(err_msg)
