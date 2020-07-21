import logging

from core.helper import get_request
from core.print_formatters import print_err_response, print_firewall_rules

logger = logging.getLogger(__name__)


def get_schain_firewall_rules(schain):
    status, payload = get_request('get_schain_firewall_rules',
                                  {'schain': schain})
    if status == 'ok':
        print_firewall_rules(payload['endpoints'])
    else:
        print_err_response(payload)
