import pytest

from node_cli.configs.routes import (
    RouteNotFoundException,
    get_route,
    route_exists,
)


def test_route_exists():
    assert route_exists('node', 'signature', 'v1')
    assert not route_exists('snode', 'mignature', 'v1')


def test_get_route():
    assert get_route('info', 'containers') == '/api/v1/info/containers'

    with pytest.raises(RouteNotFoundException):
        get_route('health', 'containers')
