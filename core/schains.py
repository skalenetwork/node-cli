import json
import logging
import pprint

from core.helper import get_request, post_request
from core.print_formatters import (
    print_dkg_statuses,
    print_err_response,
    print_firewall_rules,
    print_schains,
    print_schains_healthchecks
)


logger = logging.getLogger(__name__)


def get_schain_firewall_rules(schain: str) -> None:
    status, payload = get_request('get_schain_firewall_rules',
                                  {'schain': schain})
    if status == 'ok':
        print_firewall_rules(payload['endpoints'])
    else:
        print_err_response(payload)


def show_schains() -> None:
    status, payload = get_request('node_schains')
    if status == 'ok':
        schains = payload
        if not schains:
            print('No sChains found')
            return
        print_schains(schains)
    else:
        print_err_response(payload)


def show_dkg_info(all: bool = False) -> None:
    params = {'all': all}
    status, payload = get_request('dkg_statuses', params=params)
    if status == 'ok':
        print_dkg_statuses(payload)
    else:
        print_err_response(payload)


def show_config(name: str) -> None:
    status, payload = get_request('schain_config', {'schain-name': name})
    if status == 'ok':
        pprint.pprint(payload)
    else:
        print_err_response(payload)


def show_checks(json_format: bool = False) -> None:
    status, payload = get_request('schains_healthchecks')
    if status == 'ok':
        if not payload:
            print('No sChains found')
            return
        if json_format:
            print(json.dumps(payload))
        else:
            print_schains_healthchecks(payload)
    else:
        print_err_response(payload)


def toggle_schain_repair_mode(schain: str) -> None:
    status, payload = post_request('repair_schain', {'schain': schain})
    if status == 'ok':
        print('Schain has been set for repair')
    else:
        print_err_response(payload)
