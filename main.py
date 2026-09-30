"""
main.py - Entry point and live CLI demonstration for Intelligent Self-Healing SDN Network.

Orchestrates:
1. Topology creation & initialization
2. Centralized SDN controller path computation (Dijkstra)
3. Discrete-event packet traffic generation (SimPy)
4. Scheduled physical link fault injection
5. Explicit heartbeat-based failure detection
6. Autonomous dynamic route recomputation & traffic rerouting
7. Quantitative network KPI measurement (PDR, Loss %, Latency, MTTR)
"""

import sys
import argparse
from pathlib import Path

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import SimulationConfig
from src.simulation.traffic_simulator import TrafficSimulator


def run_live_demonstration(
    duration: float = 30.0,
    packet_rate: float = 5.0,
    failure_time: float = 10.0,
    heartbeat_interval: float = 1.0,
    routing_mode: str = "self_healing",
) -> None:
    """Executes and prints the standardized live SDN demonstration."""
    print("=" * 60)
    print("       INTELLIGENT SELF-HEALING SDN NETWORK")
    print("    Software-Defined Control Plane Simulation (Python/SimPy)")
    print("=" * 60)
    print()

    mode_label = "Self-Healing SDN (Autonomous Recovery)" if routing_mode == "self_healing" else "Static Routing (No Recovery Baseline)"
    print(f"Operational Mode: {mode_label}")
    print(f"Topology Fabric:  2 End Hosts (H1, H2), 5 SDN Switches (S1..S5)")
    print(f"Traffic Flow:     Source: H1  --->  Destination: H2")
    print(f"Simulation Window: {duration} discrete time units (Traffic Rate = {packet_rate} pkts/unit)")
    print(f"Fault Schedule:   Physical Link (S2-S3) severed at t = {failure_time:.1f}")
    print(f"Monitoring:       Heartbeat Health Polling Interval = {heartbeat_interval:.1f} units")
    print()

    cfg = SimulationConfig(
        simulation_duration=duration,
        packet_rate=packet_rate,
        failure_time=failure_time,
        heartbeat_interval=heartbeat_interval,
        routing_mode=routing_mode,
        failed_link=("S2", "S3"),
    )

    sim = TrafficSimulator(cfg)
    result = sim.run()

    init_path_str = " -> ".join(result.initial_route)
    final_path_str = " -> ".join(result.final_route)

    print("------------------------------------------------------------")
    print("INITIAL STATE (t = 0.0)")
    print("------------------------------------------------------------")
    print(f"Controller Topology Discovery: COMPLETE")
    print(f"Primary Dijkstra Path:         {init_path_str}")
    print()

    rec = result.recovery_record
    print("------------------------------------------------------------")
    print(f"FAILURE EVENT & OBSERVATION")
    print("------------------------------------------------------------")
    print(f"Physical Failure Injected at:   t = {cfg.failure_time:.2f} on Link (S2-S3)")

    if rec:
        det_time = rec["detection_time"]
        det_delay = rec["detection_delay"]
        print(f"Heartbeat Timeout Detected at: t = {det_time:.2f}")
        print(f"Explicit Detection Delay:      {det_delay:.2f} time units")
    print(f"Route Status:                  INVALIDATED ({init_path_str})")
    print()

    print("------------------------------------------------------------")
    print(f"CONTROL-PLANE ACTION: {routing_mode.upper()}")
    print("------------------------------------------------------------")
    if routing_mode == "self_healing" and rec and rec["status"] == "RECOVERED":
        reroute_time = rec["reroute_time"]
        reroute_delay = rec["reroute_delay"]
        recovery_time = rec["total_recovery_time"]

        print(f"Autonomous Recalculation:      DIJKSTRA ON ACTIVE SUBGRAPH")
        print(f"New Alternate Path Installed:  {final_path_str}")
        print(f"Traffic Reroute Triggered at:  t = {reroute_time:.2f}")
        print(f"Reroute Execution Delay:       {reroute_delay:.2f} time units")
        print(f"Total Network Recovery Time:   {recovery_time:.2f} time units")
    else:
        print(f"Static Mode Active:            No route recalculation triggered.")
        print(f"Stale Forwarding Rule:         {final_path_str} retained in switches.")
        print(f"Recovery Status:               UNRECOVERED (Ongoing packet loss)")
    print()

    m = result.summary_metrics
    print("------------------------------------------------------------")
    print("EXPERIMENTAL PERFORMANCE BENCHMARKS")
    print("------------------------------------------------------------")
    print(f"Packets Generated / Sent:      {m['packets_sent']}")
    print(f"Packets Successfully Delivered: {m['packets_received']}")
    print(f"Packets Dropped:               {m['packets_lost']}")
    print(f"Packet Loss Percentage:        {m['packet_loss_pct']:.2f} %")
    print(f"Packet Delivery Ratio (PDR):   {m['pdr_pct']:.2f} %")
    print(f"Average End-to-End Latency:    {m['avg_delay']:.4f} time units")
    print(f"Data Throughput:               {m['throughput_kbps']:.2f} kbps ({m['throughput_pps']:.2f} pkts/unit)")
    if routing_mode == "self_healing":
        print(f"Total Recovery Time:           {m['recovery_time']:.2f} time units")
    print("=" * 60)
    print()


def main():
    parser = argparse.ArgumentParser(description="Intelligent Self-Healing SDN Network Simulation Demo")
    parser.add_argument("--mode", choices=["self_healing", "static"], default="self_healing", help="Routing mode")
    parser.add_argument("--duration", type=float, default=30.0, help="Simulation duration (time units)")
    parser.add_argument("--rate", type=float, default=5.0, help="Packet traffic generation rate")
    parser.add_argument("--failure-time", type=float, default=10.0, help="Timestamp of link cut")
    args = parser.parse_args()

    run_live_demonstration(
        duration=args.duration,
        packet_rate=args.rate,
        failure_time=args.failure_time,
        routing_mode=args.mode,
    )


if __name__ == "__main__":
    main()
