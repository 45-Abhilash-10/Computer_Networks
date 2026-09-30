"""
test_metrics.py - Unit tests for metrics collection, zero-packet handling, and time series.
"""

import pytest
import pandas as pd
from src.metrics.metrics_collector import MetricsCollector
from src.simulation.packet import Packet


def test_zero_packets_safe_metrics():
    """Verify metrics collector handles empty packet logs safely without ZeroDivisionError."""
    collector = MetricsCollector(simulation_duration=30.0)
    m = collector.get_summary_metrics()

    assert m["packets_sent"] == 0
    assert m["packets_received"] == 0
    assert m["packet_loss_pct"] == 0.0
    assert m["pdr_pct"] == 0.0
    assert m["avg_delay"] == 0.0
    assert m["throughput_kbps"] == 0.0


def test_metrics_calculation_accuracy():
    """Verify correct computation of loss %, PDR %, and latency."""
    collector = MetricsCollector(simulation_duration=10.0, packet_size_bytes=1000)

    # 3 delivered, 1 dropped -> 4 sent
    for i in range(1, 4):
        p = Packet(packet_id=i, source="H1", destination="H2", creation_time=float(i))
        p.mark_delivered(delivery_time=float(i) + 1.5)
        collector.record_packet(p)

    p_drop = Packet(packet_id=4, source="H1", destination="H2", creation_time=4.0)
    p_drop.mark_dropped("S2", "LINK_DOWN")
    collector.record_packet(p_drop)

    m = collector.get_summary_metrics()
    assert m["packets_sent"] == 4
    assert m["packets_received"] == 3
    assert m["packets_lost"] == 1
    assert m["packet_loss_pct"] == 25.0
    assert m["pdr_pct"] == 75.0
    assert m["avg_delay"] == 1.5


def test_time_series_aggregation():
    """Verify time series binned dataframe generation."""
    collector = MetricsCollector(simulation_duration=10.0)
    for i in range(1, 6):
        p = Packet(packet_id=i, source="H1", destination="H2", creation_time=float(i))
        p.mark_delivered(delivery_time=float(i) + 1.0)
        collector.record_packet(p)

    ts_df = collector.get_time_series_metrics(bin_size=2.0)
    assert not ts_df.empty
    assert "time" in ts_df.columns
    assert "delivered" in ts_df.columns
