"""
test_simulation.py - Unit tests for SimPy packet generation, transit, and delivery.
"""

import pytest
from src.config import SimulationConfig
from src.simulation.traffic_simulator import TrafficSimulator
from src.simulation.packet import Packet, PacketStatus


def test_packet_creation_and_states():
    """Verify packet lifecycle state transitions and serialization."""
    pkt = Packet(packet_id=1, source="H1", destination="H2", creation_time=0.0)
    assert pkt.status == PacketStatus.GENERATED

    pkt.mark_in_transit("H1", ["H1", "S1", "H2"])
    assert pkt.status == PacketStatus.IN_TRANSIT
    assert pkt.current_node == "H1"

    pkt.mark_delivered(delivery_time=2.0)
    assert pkt.status == PacketStatus.DELIVERED
    assert pkt.delay == 2.0


def test_normal_simulation_delivery():
    """Verify 100% PDR when no faults are injected."""
    cfg = SimulationConfig(
        simulation_duration=15.0,
        packet_rate=4.0,
        failure_time=999.0,  # No failure during test
        routing_mode="self_healing",
    )
    sim = TrafficSimulator(cfg)
    result = sim.run()

    m = result.summary_metrics
    assert m["packets_sent"] > 0
    assert m["packets_received"] == m["packets_sent"]
    assert m["packet_loss_pct"] == 0.0
    assert m["pdr_pct"] == 100.0
