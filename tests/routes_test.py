import pytest
from node_cli.configs.routes import (route_exists, get_route, get_all_available_routes,
                                     RouteNotFoundException)


ALL_V1_ROUTES = [
    '/api/v1/node/info',
    '/api/v1/node/register',
    '/api/v1/node/maintenance-on',
    '/api/v1/node/maintenance-off',
    '/api/v1/node/signature',
    '/api/v1/node/send-tg-notification',
    '/api/v1/node/exit/start',
    '/api/v1/node/exit/status',
    '/api/v1/node/set-domain-name',

    '/api/v1/health/containers',
    '/api/v1/health/schains',
    '/api/v1/health/sgx',

    '/api/v1/schains/config',
    '/api/v1/schains/list',
    '/api/v1/schains/dkg-statuses',
    '/api/v1/schains/firewall-rules',
    '/api/v1/schains/repair',
    '/api/v1/schains/get',

    '/api/v1/ssl/status',
    '/api/v1/ssl/upload',

    '/api/v1/wallet/info',
    '/api/v1/wallet/send-eth'
]


def test_route_exists():
    assert route_exists('node', 'signature', 'v1')
    assert not route_exists('snode', 'mignature', 'v1')


def test_get_route():
    repair_route = get_route('schains', 'repair')
    assert repair_route == '/api/v1/schains/repair'

    with pytest.raises(RouteNotFoundException):
        get_route('schains', 'refair')


def test_get_all_available_routes():
    assert get_all_available_routes() == ALL_V1_ROUTES
