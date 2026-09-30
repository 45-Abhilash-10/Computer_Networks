"""
baseline.py - Executes and compares Static Routing vs Self-Healing SDN.

Provides direct comparative analysis:
- Static Routing: No controller recovery; packets targeting failed link are dropped.
- Self-Healing SDN: Autonomous heartbeat detection, Dijkstra recalculation, and rerouting.
"""

from typing import Dict, Any, Tuple
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import matplotlib.pyplot as plt

from src.config import SimulationConfig, FIGURES_DIR, METRICS_DIR
from src.simulation.traffic_simulator import TrafficSimulator, SimulationResult


def run_baseline_comparison(
    simulation_duration: float = 30.0,
    packet_rate: float = 5.0,
    failure_time: float = 10.0,
    heartbeat_interval: float = 1.0,
    save_outputs: bool = True,
) -> Tuple[SimulationResult, SimulationResult, pd.DataFrame]:
    """
    Runs both Static and Self-Healing simulations with identical parameters
    and compiles comparative benchmark tables and charts.

    Returns:
        (static_result, self_healing_result, comparison_dataframe)
    """
    # 1. Run Static Baseline
    cfg_static = SimulationConfig(
        simulation_duration=simulation_duration,
        packet_rate=packet_rate,
        failure_time=failure_time,
        heartbeat_interval=heartbeat_interval,
        routing_mode="static",
    )
    sim_static = TrafficSimulator(cfg_static)
    res_static = sim_static.run()

    # 2. Run Self-Healing SDN
    cfg_sh = SimulationConfig(
        simulation_duration=simulation_duration,
        packet_rate=packet_rate,
        failure_time=failure_time,
        heartbeat_interval=heartbeat_interval,
        routing_mode="self_healing",
    )
    sim_sh = TrafficSimulator(cfg_sh)
    res_sh = sim_sh.run()

    # 3. Create Comparison DataFrame
    m_stat = res_static.summary_metrics
    m_sh = res_sh.summary_metrics

    metrics_rows = [
        {"Metric": "Routing Mode", "Static Baseline": "Static (No Recovery)", "Self-Healing SDN": "Autonomous Dijkstra Reroute"},
        {"Metric": "Packets Sent", "Static Baseline": m_stat["packets_sent"], "Self-Healing SDN": m_sh["packets_sent"]},
        {"Metric": "Packets Received", "Static Baseline": m_stat["packets_received"], "Self-Healing SDN": m_sh["packets_received"]},
        {"Metric": "Packets Lost", "Static Baseline": m_stat["packets_lost"], "Self-Healing SDN": m_sh["packets_lost"]},
        {"Metric": "Packet Loss (%)", "Static Baseline": m_stat["packet_loss_pct"], "Self-Healing SDN": m_sh["packet_loss_pct"]},
        {"Metric": "Packet Delivery Ratio (%)", "Static Baseline": m_stat["pdr_pct"], "Self-Healing SDN": m_sh["pdr_pct"]},
        {"Metric": "Average Delay (units)", "Static Baseline": m_stat["avg_delay"], "Self-Healing SDN": m_sh["avg_delay"]},
        {"Metric": "Throughput (kbps)", "Static Baseline": m_stat["throughput_kbps"], "Self-Healing SDN": m_sh["throughput_kbps"]},
        {"Metric": "Detection Delay (units)", "Static Baseline": "N/A", "Self-Healing SDN": m_sh["detection_time"]},
        {"Metric": "Reroute Delay (units)", "Static Baseline": "N/A", "Self-Healing SDN": m_sh["reroute_time"]},
        {"Metric": "Total Recovery Time (units)", "Static Baseline": "Failed / Never", "Self-Healing SDN": m_sh["recovery_time"]},
    ]

    df_comp = pd.DataFrame(metrics_rows)
    df_comp["Static Baseline"] = df_comp["Static Baseline"].astype(str)
    df_comp["Self-Healing SDN"] = df_comp["Self-Healing SDN"].astype(str)

    if save_outputs:
        # Save CSV
        csv_path = METRICS_DIR / "baseline_comparison.csv"
        df_comp.to_csv(csv_path, index=False)

        # Generate and save comparison bar chart
        _generate_comparison_chart(m_stat, m_sh, FIGURES_DIR / "baseline_comparison.png")

    return res_static, res_sh, df_comp


def _generate_comparison_chart(m_stat: Dict[str, Any], m_sh: Dict[str, Any], output_path: Path) -> None:
    """Generates comparative bar chart for static vs self-healing metrics."""
    metrics_to_plot = ["PDR (%)", "Packet Loss (%)", "Throughput (kbps)"]
    static_vals = [m_stat["pdr_pct"], m_stat["packet_loss_pct"], m_stat["throughput_kbps"]]
    sh_vals = [m_sh["pdr_pct"], m_sh["packet_loss_pct"], m_sh["throughput_kbps"]]

    x = range(len(metrics_to_plot))
    width = 0.35

    plt.figure(figsize=(9, 5))
    plt.bar([p - width / 2 for p in x], static_vals, width, label="Static (No Recovery)", color="#d9534f")
    plt.bar([p + width / 2 for p in x], sh_vals, width, label="Self-Healing SDN", color="#5cb85c")

    plt.xlabel("Key Performance Metrics", fontweight="bold")
    plt.ylabel("Value", fontweight="bold")
    plt.title("SDN Failure Recovery: Static Routing vs Self-Healing SDN", fontsize=12, fontweight="bold")
    plt.xticks(x, metrics_to_plot)
    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


if __name__ == "__main__":
    print("Running Baseline Comparison...")
    _, _, comp_df = run_baseline_comparison()
    print(comp_df.to_string(index=False))
