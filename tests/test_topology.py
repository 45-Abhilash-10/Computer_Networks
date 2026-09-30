"""
test_topology.py - Unit tests for topology creation, link states, and graph querying.
"""

import pytest
import networkx as nx
from src.topology.topology_manager import TopologyManager


def test_topology_node_and_edge_counts():
    """Verify canonical topology has 7 nodes (2 hosts, 5 switches) and 7 links."""
    tm = TopologyManager()
    graph = tm.get_graph()

    assert len(graph.nodes) == 7
    assert len(graph.edges) == 7
    assert sorted(tm.get_hosts()) == ["H1", "H2"]
    assert sorted(tm.get_switches()) == ["S1", "S2", "S3", "S4", "S5"]


def test_link_attributes():
    """Verify link attributes (bandwidth, delay, cost, status)."""
    tm = TopologyManager(default_bandwidth=100.0, default_delay=0.5)
    graph = tm.get_graph()

    for u, v, data in graph.edges(data=True):
        assert data["bandwidth"] == 100.0
        assert data["delay"] == 0.5
        assert data["cost"] == 1.0
        assert data["status"] == "UP"


def test_link_status_modification():
    """Verify setting link status to DOWN and resetting back to UP."""
    tm = TopologyManager()
    assert tm.get_link_status("S2", "S3") == "UP"

    tm.set_link_status("S2", "S3", "DOWN")
    assert tm.get_link_status("S2", "S3") == "DOWN"

    # Active subgraph should exclude DOWN links
    active_g = tm.get_active_graph()
    assert not active_g.has_edge("S2", "S3")
    assert len(active_g.edges) == 6

    # Reset
    tm.reset_all_links()
    assert tm.get_link_status("S2", "S3") == "UP"
    assert tm.get_active_graph().has_edge("S2", "S3")


def test_node_positions_exist():
    """Verify all 7 nodes have designated 2D coordinates."""
    tm = TopologyManager()
    positions = tm.get_node_positions()
    assert len(positions) == 7
    assert "H1" in positions and "H2" in positions
