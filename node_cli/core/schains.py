import logging
import pprint

from typing import Optional

from node_cli.utils.helper import get_request, post_request, error_exit
from node_cli.utils.exit_codes import CLIExitCodes
from node_cli.utils.print_formatters import (
    print_dkg_statuses,
    print_firewall_rules,
    print_schain_info,
    print_schains
)


logger = logging.getLogger(__name__)

BLUEPRINT_NAME = 'schains'


def get_schain_firewall_rules(schain: str) -> None:
    status, payload = get_request(
        blueprint=BLUEPRINT_NAME,
        method='firewall-rules',
        params={'schain_name': schain}
    )
    if status == 'ok':
        print_firewall_rules(payload['endpoints'])
    else:
        error_exit(payload, exit_code=CLIExitCodes.BAD_API_RESPONSE)


def show_schains() -> None:
    status, payload = get_request(
        blueprint=BLUEPRINT_NAME,
        method='list'
    )
    if status == 'ok':
        schains = payload
        if not schains:
            print('No sChains found')
            return
        print_schains(schains)
    else:
        error_exit(payload, exit_code=CLIExitCodes.BAD_API_RESPONSE)


def show_dkg_info(all_: bool = False) -> None:
    params = {'all': all_}
    status, payload = get_request(
        blueprint=BLUEPRINT_NAME,
        method='dkg-statuses',
        params=params
    )
    if status == 'ok':
        print_dkg_statuses(payload)
    else:
        error_exit(payload, exit_code=CLIExitCodes.BAD_API_RESPONSE)


def show_config(name: str) -> None:
    status, payload = get_request(
        blueprint=BLUEPRINT_NAME,
        method='config',
        params={'schain_name': name}
    )
    if status == 'ok':
        pprint.pprint(payload)
    else:
        error_exit(payload, exit_code=CLIExitCodes.BAD_API_RESPONSE)


def toggle_schain_repair_mode(
    schain: str,
    snapshot_from: Optional[str] = None
) -> None:
    json_params = {'schain_name': schain}
    if snapshot_from:
        json_params.update({'snapshot_from': snapshot_from})
    status, payload = post_request(
        blueprint=BLUEPRINT_NAME,
        method='repair',
        json=json_params
    )
    if status == 'ok':
        print('Schain has been set for repair')
    else:
        error_exit(payload, exit_code=CLIExitCodes.BAD_API_RESPONSE)


def describe(schain: str, raw=False) -> None:
    status, payload = get_request(
        blueprint=BLUEPRINT_NAME,
        method='get',
        params={'schain_name': schain}
    )
    if status == 'ok':
        print_schain_info(payload, raw=raw)
    else:
        error_exit(payload, exit_code=CLIExitCodes.BAD_API_RESPONSE)
