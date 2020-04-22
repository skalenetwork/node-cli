import logging

import requests

from configs import ROUTES
from core.helper import (construct_url, get_request,
                         post_request, print_err_response)

logger = logging.getLogger(__name__)


def get(url_name, params=None):
    # TODO: move to core.helper
    url = construct_url(ROUTES[url_name])

    response = get_request(url, params)
    if response is None:
        return None

    if response.status_code != requests.codes.ok:  # pylint: disable=no-member
        print('Request failed, status code:', response.status_code)
        return None

    try:
        response_json = response.json()
    except Exception as err:
        logger.error('Response parsing failed', exc_info=err)
        return {'errors': 'Response parsing failed. Check skale_admin container logs'}

    json_data = response_json['data']
    if json_data['status'] == 'ok':
        return json_data['payload']
    else:
        print_err_response(json_data)
        return None


def post(url_name, json=None, files=None):
    url = construct_url(ROUTES[url_name])
    response = post_request(url, json=json, files=files)
    if response is None:
        return None
    try:
        response_json = response.json()
    except Exception as err:
        logger.error('Response parsing failed', exc_info=err)
        return {'errors': ['Response parsing failed. Check skale_admin container logs']}
    json_data = response_json['data']
    if json_data['status'] == 'ok':
        return json_data['payload']
    else:
        print_err_response(json_data)
        return None


def get_schain_firewall_rules(schain):
    response = get('get_schain_firewall_rules', {'schain': schain})
    return response['endpoints']


def turn_on_schain_firewall_rules(schain):
    post('turn_on_schain_firewall_rules', {'schain': schain})


def turn_off_schain_firewall_rules(schain):
    post('turn_off_schain_firewall_rules', {'schain': schain})
