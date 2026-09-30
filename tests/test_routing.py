"""
test_routing.py - Unit tests for Dijkstra routing, route validation, and alternate paths.
"""

import pytest
from src.topology.topology_manager import TopologyManager
from src.routing.dijkstra_router import DijkstraRouter, NoPathError


def test_dijkstra_primary_route():
    """Verify primary route H1 -> S1 -> S2 -> S3 -> H2 under normal conditions."""
    tm = TopologyManager()
    router = DijkstraRouter()
    active_g = tm.get_active_graph()

    route = router.calculate_route(active_g, "H1", "H2")
    assert route == ["H1", "S1", "S2", "S3", "H2"]


def test_route_validation():
    """Verify route validity checks when links are UP vs DOWN."""
    tm = TopologyManager()
    router = DijkstraRouter()

    primary = ["H1", "S1", "S2", "S3", "H2"]
    assert router.is_route_valid(tm.get_graph(), primary) is True

    # Break link S2-S3
    tm.set_link_status("S2", "S3", "DOWN")
    assert router.is_route_valid(tm.get_graph(), primary) is False


def test_dijkstra_alternate_route_calculation():
    """Verify alternate route H1 -> S1 -> S4 -> S5 -> S3 -> H2 when S2-S3 is cut."""
    tm = TopologyManager()
    router = DijkstraRouter()

    # Fail primary link S2-S3
    tm.set_link_status("S2", "S3", "DOWN")
    active_g = tm.get_active_graph()

    alt_route = router.calculate_route(active_g, "H1", "H2")
    assert alt_route == ["H1", "S1", "S4", "S5", "S3", "H2"]


def test_no_path_handling():
    """Verify NoPathError is raised cleanly when network is fully partitioned."""
    tm = TopologyManager()
    router = DijkstraRouter()

    # Cut both paths: S1-S2 and S1-S4
    tm.set_link_status("S1", "S2", "DOWN")
    tm.set_link_status("S1", "S4", "DOWN")
    active_g = tm.get_active_graph()

    with pytest.raises(NoPathError):
        router.calculate_route(active_g, "H1", "H2")
