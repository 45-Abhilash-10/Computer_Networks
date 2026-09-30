"""
test_failure_recovery.py - Unit tests for failure injection, detection, and self-healing.
"""

import pytest
from src.config import SimulationConfig
from src.topology.topology_manager import TopologyManager
from src.routing.dijkstra_router import DijkstraRouter
from src.controller.sdn_controller import SDNController
from src.simulation.traffic_simulator import TrafficSimulator


def test_controller_handles_failure_and_reroutes():
    """Verify SDN controller updates topology, invalidates route, and installs alternate path."""
    tm = TopologyManager()
    router = DijkstraRouter()
    ctrl = SDNController(topology_manager=tm, router=router, routing_mode="self_healing")

    # Initial flow installed
    route_init = ctrl.get_route("H1", "H2")
    assert route_init == ["H1", "S1", "S2", "S3", "H2"]

    # Notify controller of S2-S3 failure at t=11.0
    rec = ctrl.handle_failure_notification("S2", "S3", detection_time=11.0)
    assert rec["status"] == "RECOVERED"
    assert rec["old_routes"][("H1", "H2")] == ["H1", "S1", "S2", "S3", "H2"]
    assert rec["new_routes"][("H1", "H2")] == ["H1", "S1", "S4", "S5", "S3", "H2"]

    # Verify query returns new alternate path
    assert ctrl.get_route("H1", "H2") == ["H1", "S1", "S4", "S5", "S3", "H2"]


def test_static_routing_leaves_stale_path():
    """Verify static routing controller does not reroute upon failure."""
    tm = TopologyManager()
    router = DijkstraRouter()
    ctrl = SDNController(topology_manager=tm, router=router, routing_mode="static")

    ctrl.get_route("H1", "H2")
    rec = ctrl.handle_failure_notification("S2", "S3", detection_time=11.0)

    assert rec["status"] == "UNRECOVERED"
    # Route remains stale
    assert ctrl.get_route("H1", "H2") == ["H1", "S1", "S2", "S3", "H2"]


def test_self_healing_vs_static_simulation():
    """Verify self-healing simulation achieves significantly higher PDR than static mode."""
    cfg_sh = SimulationConfig(simulation_duration=25.0, packet_rate=5.0, failure_time=10.0, routing_mode="self_healing")
    sim_sh = TrafficSimulator(cfg_sh)
    res_sh = sim_sh.run()

    cfg_stat = SimulationConfig(simulation_duration=25.0, packet_rate=5.0, failure_time=10.0, routing_mode="static")
    sim_stat = TrafficSimulator(cfg_stat)
    res_stat = sim_stat.run()

    # Self-healing must have substantially higher PDR and lower packet loss
    assert res_sh.summary_metrics["pdr_pct"] > 80.0
    assert res_stat.summary_metrics["pdr_pct"] < 50.0
    assert res_sh.summary_metrics["packet_loss_pct"] < res_stat.summary_metrics["packet_loss_pct"]
