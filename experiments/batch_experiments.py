"""
batch_experiments.py - Multi-scenario experiment suite with statistical aggregation.

Executes:
1. Normal operation (no fault)
2. Standard link failure (S2-S3 at t=10)
3. Failure timing sweep (t=5, 10, 15)
4. Traffic rate variation (2, 5, 10, 15 pkts/unit)
5. Static vs Self-Healing comparison across multiple trials

Aggregates Mean, Std, Min, Max for key metrics and saves summary CSV.
"""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np
from src.config import SimulationConfig, METRICS_DIR
from src.simulation.traffic_simulator import TrafficSimulator


def run_scenario(
    scenario_name: str,
    duration: float = 30.0,
    packet_rate: float = 5.0,
    failure_time: float = 10.0,
    routing_mode: str = "self_healing",
    trials: int = 5,
) -> pd.DataFrame:
    """Executes multiple trials for a specific parameter setting."""
    records = []
    for t in range(1, trials + 1):
        cfg = SimulationConfig(
            simulation_duration=duration,
            packet_rate=packet_rate,
            failure_time=failure_time,
            routing_mode=routing_mode,
            random_seed=100 + t * 13,
        )
        sim = TrafficSimulator(cfg)
        res = sim.run()
        m = res.summary_metrics

        records.append({
            "scenario": scenario_name,
            "trial": t,
            "routing_mode": routing_mode,
            "packet_rate": packet_rate,
            "failure_time": failure_time,
            "packets_sent": m["packets_sent"],
            "packets_received": m["packets_received"],
            "packets_lost": m["packets_lost"],
            "packet_loss_pct": m["packet_loss_pct"],
            "pdr_pct": m["pdr_pct"],
            "avg_delay": m["avg_delay"],
            "throughput_kbps": m["throughput_kbps"],
            "recovery_time": m["recovery_time"],
        })
    return pd.DataFrame(records)


def main():
    print("=" * 65)
    print("Executing Comprehensive SDN Simulation Batch Experiment Suite")
    print("=" * 65)

    all_data = []

    # Scenario 1: Normal Network (No Failure)
    print("\n[1/5] Running Scenario: Normal Operation (No Injected Failure)...")
    df_normal = run_scenario("1_Normal_No_Failure", failure_time=999.0, routing_mode="self_healing")
    all_data.append(df_normal)

    # Scenario 2: Standard Single Link Cut (Self-Healing)
    print("[2/5] Running Scenario: Standard Link Failure (S2-S3 Cut with Self-Healing)...")
    df_standard = run_scenario("2_Standard_Self_Healing", failure_time=10.0, routing_mode="self_healing")
    all_data.append(df_standard)

    # Scenario 3: Standard Single Link Cut (Static Routing)
    print("[3/5] Running Scenario: Standard Link Failure (Static Routing / No Healing)...")
    df_static = run_scenario("3_Standard_Static_Baseline", failure_time=10.0, routing_mode="static")
    all_data.append(df_static)

    # Scenario 4: Traffic Load Sweep (2, 5, 10, 15 pkts/unit)
    print("[4/5] Running Scenario: Traffic Load Sweep...")
    for rate in [2.0, 10.0, 15.0]:
        df_rate = run_scenario(f"4_Load_Rate_{int(rate)}", packet_rate=rate, failure_time=10.0, routing_mode="self_healing")
        all_data.append(df_rate)

    # Scenario 5: Failure Timing Sweep (t=5, 15)
    print("[5/5] Running Scenario: Failure Timing Sweep...")
    for f_time in [5.0, 15.0]:
        df_time = run_scenario(f"5_Fault_At_t_{int(f_time)}", failure_time=f_time, routing_mode="self_healing")
        all_data.append(df_time)

    # Combine all trials
    df_combined = pd.concat(all_data, ignore_index=True)
    raw_path = METRICS_DIR / "batch_experiments_raw.csv"
    df_combined.to_csv(raw_path, index=False)
    print(f"\nAll trial raw records saved to: {raw_path}")

    # Compute Statistical Summary (Mean, Std, Min, Max)
    metrics_to_agg = ["packet_loss_pct", "pdr_pct", "avg_delay", "throughput_kbps", "recovery_time"]
    agg_funcs = ["mean", "std", "min", "max"]

    summary = df_combined.groupby(["scenario", "routing_mode"])[metrics_to_agg].agg(agg_funcs).round(2)
    summary_path = METRICS_DIR / "batch_experiments_summary.csv"
    summary.to_csv(summary_path)
    print(f"Aggregated summary statistics saved to: {summary_path}")
    print("\nAggregated Results:")
    print(summary)


if __name__ == "__main__":
    main()
