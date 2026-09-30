"""
run_experiment.py - Executes a standardized SDN failure recovery experiment.

Runs repeatable simulation trials and logs structured metrics to CSV.
Usage:
    python experiments/run_experiment.py [--trials N] [--duration D]
"""

import sys
from pathlib import Path
import argparse

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from src.config import SimulationConfig, METRICS_DIR
from src.simulation.traffic_simulator import TrafficSimulator


def run_single_experiment(
    trial: int = 1,
    experiment_id: str = "EXP_STANDARD",
    duration: float = 30.0,
    packet_rate: float = 5.0,
    failure_time: float = 10.0,
    failed_link: tuple = ("S2", "S3"),
    routing_mode: str = "self_healing",
    seed: int = 42,
) -> dict:
    """Executes a single simulation trial and returns a formatted row dictionary."""
    cfg = SimulationConfig(
        simulation_duration=duration,
        packet_rate=packet_rate,
        failure_time=failure_time,
        failed_link=failed_link,
        routing_mode=routing_mode,
        random_seed=seed,
    )
    sim = TrafficSimulator(cfg)
    result = sim.run()
    m = result.summary_metrics

    return {
        "experiment_id": experiment_id,
        "trial": trial,
        "routing_mode": routing_mode,
        "failure_type": "LINK_FAILURE",
        "failed_link": f"{failed_link[0]}-{failed_link[1]}",
        "failure_time": failure_time,
        "traffic_rate": packet_rate,
        "duration": duration,
        "packets_sent": m["packets_sent"],
        "packets_received": m["packets_received"],
        "packets_lost": m["packets_lost"],
        "packet_loss_pct": m["packet_loss_pct"],
        "pdr_pct": m["pdr_pct"],
        "avg_delay": m["avg_delay"],
        "throughput_kbps": m["throughput_kbps"],
        "detection_time": m["detection_time"],
        "reroute_time": m["reroute_time"],
        "recovery_time": m["recovery_time"],
    }


def main():
    parser = argparse.ArgumentParser(description="Run SDN Self-Healing Experiment")
    parser.add_argument("--trials", type=int, default=5, help="Number of experimental trials")
    parser.add_argument("--duration", type=float, default=30.0, help="Simulation duration (time units)")
    parser.add_argument("--rate", type=float, default=5.0, help="Packet generation rate")
    args = parser.parse_args()

    print("=" * 60)
    print(f"Running Standard Experiment: {args.trials} Trials (Duration={args.duration})")
    print("=" * 60)

    records = []
    for t in range(1, args.trials + 1):
        seed = 42 + t * 7
        # Run self-healing
        rec_sh = run_single_experiment(
            trial=t,
            experiment_id="EXP_SELF_HEALING",
            duration=args.duration,
            packet_rate=args.rate,
            routing_mode="self_healing",
            seed=seed,
        )
        records.append(rec_sh)

        # Run static baseline
        rec_stat = run_single_experiment(
            trial=t,
            experiment_id="EXP_STATIC_BASELINE",
            duration=args.duration,
            packet_rate=args.rate,
            routing_mode="static",
            seed=seed,
        )
        records.append(rec_stat)

    df_results = pd.DataFrame(records)
    csv_path = METRICS_DIR / "experiment_results.csv"
    df_results.to_csv(csv_path, index=False)
    print(f"Results successfully saved to: {csv_path}")
    print("\nSummary Results Preview:")
    print(df_results[["experiment_id", "trial", "packets_sent", "pdr_pct", "packet_loss_pct", "recovery_time"]].to_string(index=False))


if __name__ == "__main__":
    main()
