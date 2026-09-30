"""
metrics_collector.py - Gathers and computes SDN performance and recovery metrics.

Calculates:
- Packets Sent, Received, Dropped
- Packet Loss Percentage
- Packet Delivery Ratio (PDR)
- Average End-to-End Latency
- Throughput (packets/sec and bps)
- Detection Time, Reroute Time, Recovery Time
- Time-series sliding window telemetry for analytics and dashboard charts
"""

from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from src.simulation.packet import Packet, PacketStatus


class MetricsCollector:
    """Collects, aggregates, and computes experimental SDN network metrics."""

    def __init__(self, simulation_duration: float = 30.0, packet_size_bytes: int = 1024):
        self.simulation_duration = max(0.1, simulation_duration)
        self.packet_size_bytes = packet_size_bytes
        self.packets: List[Packet] = []
        self.recovery_records: List[Dict[str, Any]] = []

    def record_packet(self, packet: Packet) -> None:
        """Records a completed (delivered or dropped) packet."""
        self.packets.append(packet)

    def record_recovery(self, recovery_data: Dict[str, Any]) -> None:
        """Records recovery timing metadata from RecoveryEngine."""
        self.recovery_records.append(recovery_data)

    def get_summary_metrics(self) -> Dict[str, Any]:
        """
        Calculates all primary project KPIs.
        Safe against zero-packet edge cases.
        """
        sent = len(self.packets)
        delivered = sum(
            1 for p in self.packets if p.status in (PacketStatus.DELIVERED, PacketStatus.REROUTED)
        )
        dropped = sum(1 for p in self.packets if p.status == PacketStatus.DROPPED)

        pdr = (delivered / sent * 100.0) if sent > 0 else 0.0
        loss_pct = (dropped / sent * 100.0) if sent > 0 else 0.0

        delays = [p.delay for p in self.packets if p.delay is not None]
        avg_delay = float(np.mean(delays)) if delays else 0.0
        min_delay = float(np.min(delays)) if delays else 0.0
        max_delay = float(np.max(delays)) if delays else 0.0

        # Throughput: bits per simulation time unit
        total_delivered_bits = delivered * self.packet_size_bytes * 8
        throughput_bps = total_delivered_bits / self.simulation_duration
        throughput_pps = delivered / self.simulation_duration

        # Recovery metrics from latest recorded recovery event
        detection_delay = 0.0
        reroute_delay = 0.0
        recovery_time = 0.0

        if self.recovery_records:
            latest = self.recovery_records[-1]
            detection_delay = latest.get("detection_delay") or 0.0
            reroute_delay = latest.get("reroute_delay") or 0.0
            recovery_time = latest.get("total_recovery_time") or 0.0

        return {
            "packets_sent": sent,
            "packets_received": delivered,
            "packets_lost": dropped,
            "packet_loss_pct": round(loss_pct, 2),
            "pdr_pct": round(pdr, 2),
            "avg_delay": round(avg_delay, 4),
            "min_delay": round(min_delay, 4),
            "max_delay": round(max_delay, 4),
            "throughput_pps": round(throughput_pps, 2),
            "throughput_kbps": round(throughput_bps / 1000.0, 2),
            "detection_time": round(detection_delay, 3),
            "reroute_time": round(reroute_delay, 3),
            "recovery_time": round(recovery_time, 3),
        }

    def get_packets_dataframe(self) -> pd.DataFrame:
        """Returns all packet records as a structured Pandas DataFrame."""
        if not self.packets:
            return pd.DataFrame(columns=[
                "packet_id", "source", "destination", "creation_time",
                "delivery_time", "status", "delay", "route", "drop_reason", "is_rerouted"
            ])
        return pd.DataFrame([p.to_dict() for p in self.packets])

    def get_time_series_metrics(self, bin_size: float = 1.0) -> pd.DataFrame:
        """
        Bins packet events over simulation time intervals to produce
        throughput, loss, and delay trajectories (before, during, and after failure).
        """
        if not self.packets:
            return pd.DataFrame(columns=["time_bin", "sent", "delivered", "dropped", "pdr", "avg_delay"])

        df = self.get_packets_dataframe()
        num_bins = int(np.ceil(self.simulation_duration / bin_size))
        bins = [i * bin_size for i in range(num_bins + 1)]
        df["time_bin"] = pd.cut(df["creation_time"], bins=bins, right=False)

        grouped = df.groupby("time_bin", observed=False)
        ts_data = []

        for interval, group in grouped:
            t_start = interval.left if hasattr(interval, "left") else 0.0
            total_sent = len(group)
            total_delivered = sum(group["status"].isin([PacketStatus.DELIVERED.value, PacketStatus.REROUTED.value]))
            total_dropped = sum(group["status"] == PacketStatus.DROPPED.value)
            bin_pdr = (total_delivered / total_sent * 100.0) if total_sent > 0 else 0.0
            valid_delays = group["delay"].dropna()
            bin_delay = valid_delays.mean() if not valid_delays.empty else 0.0

            ts_data.append({
                "time": float(t_start),
                "sent": total_sent,
                "delivered": total_delivered,
                "dropped": total_dropped,
                "pdr": round(bin_pdr, 2),
                "avg_delay": round(bin_delay, 4),
            })

        return pd.DataFrame(ts_data)
