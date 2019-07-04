import pickle
import yaml
import requests
from functools import wraps
import urllib.parse

from readsettings import ReadSettings
from core.config import CONFIG_FILEPATH, TEXT_FILE, SKALE_NODE_UI_LOCALHOST, SKALE_NODE_UI_PORT, \
    LONG_LINE, URLS

config = ReadSettings(CONFIG_FILEPATH)


def safe_get_config(config, key):
    try:
        return config[key]
    except KeyError as e:
        # print(f'No such key in config: {key}')
        return None


def login_required(f):
    @wraps(f)
    def inner(*args, **kwargs):
        cookies_text = safe_get_config(config, 'cookies')
        if not cookies_text:
            TEXTS = safe_load_texts()
            print(TEXTS['service']['unauthorized'])
        else:
            return f(*args, **kwargs)

    return inner


def safe_load_texts():
    with open(TEXT_FILE, 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)


def get_node_creds(config):
    TEXTS = safe_load_texts()
    host = safe_get_config(config, 'host')
    if not host:
        host = get_localhost_endpoint()
    cookies_text = safe_get_config(config, 'cookies')
    if not host or not cookies_text:
        raise Exception(TEXTS['service']['no_node_host'])
    cookies = pickle.loads(cookies_text)
    return host, cookies


def construct_url(host, url):
    return urllib.parse.urljoin(host, url)


def get_response_data(response):
    json = response.json()
    return json['data']


def clean_cookies(config):
    if safe_get_config(config, 'cookies'):
        del config["cookies"]


def abort_if_false(ctx, param, value):
    if not value:
        ctx.abort()


def server_only(f):
    @wraps(f)
    def inner(*args, **kwargs):
        # todo: implement check that local node exists
        return f(*args, **kwargs)

    return inner


def get_localhost_endpoint():
    return f'{SKALE_NODE_UI_LOCALHOST}:{SKALE_NODE_UI_PORT}'


def get_request(url, cookies=None, params=None):
    try:
        return requests.get(url, cookies=cookies, params=params)
    except requests.exceptions.ConnectionError as e:
        # todo: log error
        print(f'Could not connect to {url}')
        return None


def post_request(url, json, cookies=None):
    try:
        return requests.post(url, json=json, cookies=cookies)
    except requests.exceptions.ConnectionError as e:
        # todo: log error
        print(f'Could not connect to {url}')
        return None


def print_err_response(err_response):
    print(LONG_LINE)
    for error in err_response['errors']:
        print(error)
    print(LONG_LINE)


def get(url_name, params=None):
    host, cookies = get_node_creds(config)
    url = construct_url(host, URLS[url_name])

    response = get_request(url, cookies, params)
    if response is None:
        return None

    if response.status_code != requests.codes.ok:
        print('Request failed, status code:', response.status_code)
        return None

    json = response.json()
    if json['res'] != 1:
        print_err_response(response.json())
        return None
    else:
        return json['data']