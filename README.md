# Intelligent Self-Healing SDN Network
### Software-Based SDN Control-Plane Simulation, Fault Detection & Autonomous Dynamic Recovery

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests Passing](https://img.shields.io/badge/pytest-16%20passed-brightgreen.svg)]()
[![Framework](https://img.shields.io/badge/Framework-SimPy%20%7C%20NetworkX%20%7C%20Streamlit-orange.svg)]()

---

> **Important Technical Positioning:**  
> This project is a **software-based SDN control-plane simulation** implemented in Python. It models the core architectural principles of Software-Defined Networking (centralized topology discovery, flow rule programming, explicit heartbeat health monitoring, and dynamic route recalculation) using `NetworkX` and `SimPy`. It does **not** rely on Mininet, OpenFlow physical hardware, or Open vSwitch.

---

## 1. Problem Statement & Motivation
In modern enterprise networks and cloud data centers, fiber disruptions, transceiver degradation, and link failures occur constantly. In legacy networks governed by distributed routing protocols (OSPF, BGP), every router must independently detect link cuts, flood Link State Advertisements (LSAs), and re-converge. This distributed convergence often takes seconds to minutes, dropping thousands of inflight packets.

Software-Defined Networking (SDN) promises an elegant remedy: by logically centralizing network visibility into a programmable software controller, the controller can observe physical failures, recompute loop-free forwarding paths, and install new forwarding rules dynamically.

This project delivers an integrated experimental framework that proves and quantifies this advantage through discrete-event packet simulation, explicit heartbeat failure detection, and empirical comparison against a static-routing baseline.

---

## 2. Core Project Objectives
1. **Network Topology Modeling:** Build graph-based network topologies with explicit host/switch classification and physical link parameters (`bandwidth`, `delay`, `cost`, `status`).
2. **Centralized SDN Controller Abstraction:** Maintain global network graph state, program flow tables, process failure telemetry, and invalidate stale paths.
3. **Shortest-Path Routing:** Calculate optimal paths using Dijkstra's shortest path algorithm over the active operational subgraph.
4. **Packet-Level Simulation:** Model discrete-event packet generation, hop-by-hop link traversal, and packet drops during outages using SimPy.
5. **Controlled Fault Injection:** Schedule precise physical link cuts during active data-plane transmission.
6. **Explicit Failure Detection:** Simulate periodic heartbeat polling to quantify the delay between physical failure inception and controller notification.
7. **Autonomous Dynamic Self-Healing:** Invalidate broken routes, compute alternate paths, install new flow rules, and reroute traffic without manual intervention.
8. **Empirical Baseline Comparison:** Benchmark Self-Healing SDN directly against a Static Routing baseline.
9. **Interactive Dashboard & Analytics:** Provide a full Streamlit + Plotly visual interface and repeatable multi-trial experiment suites.

---

## 3. System Architecture & Workflow

The platform follows the classic **MAPE-K** (Monitor, Analyze, Plan, Execute, Knowledge) autonomic loop:

```
                    +-------------------+
                    | Network Topology  | (NetworkX 2-Host, 5-Switch Fabric)
                    +---------+---------+
                              |
                              v
                    +-------------------+
                    |  SDN Controller   | (Global Graph, Flow Table, Event Log)
                    +---------+---------+
                              |
                              v
                    +-------------------+
                    | Dijkstra Router   | (Shortest Path over Active Subgraph)
                    +---------+---------+
                              |
                              v
                    +-------------------+
                    | SimPy Data Plane  | (Packet Generation & Hop Traversal)
                    +---------+---------+
                              |
                              v
                    +-------------------+
                    | Failure Injector  | (Physical Link Severed at t = 10.0)
                    +---------+---------+
                              |
                              v
                    +-------------------+
                    | Failure Detector  | (Heartbeat Polling at Interval = 1.0)
                    +---------+---------+
                              |
                              v
                    +-------------------+
                    | Route Invalidator | (H1-S1-S2-S3-H2 marked INVALID)
                    +---------+---------+
                              |
                              v
                    +-------------------+
                    |  Recovery Engine  | (Alternate Path H1-S1-S4-S5-S3-H2 Installed)
                    +---------+---------+
                              |
                              v
                    +-------------------+
                    | Metrics Collector | (PDR, Loss %, Delay, MTTR)
                    +---------+---------+
                              |
             +----------------+----------------+
             |                                 |
             v                                 v
     +---------------+                 +---------------+
     |  Streamlit    |                 |   Analytics   |
     |   Dashboard   |                 | (Pandas/Plotly|
     +---------------+                 +---------------+
```

---

## 4. The Demonstration Network Topology

```
             S2 (Cost=1)
            /  \
           /    \
H1 —— S1        S3 —— H2
       \        /
        \      /
         S4 —— S5 (Cost=1 each)
```

- **Normal Primary Path (Cost = 4):**
  $$H1 \longrightarrow S1 \longrightarrow S2 \longrightarrow S3 \longrightarrow H2$$
- **Physical Failure Event (Link S2-S3 severed):**
  $$H1 \longrightarrow S1 \longrightarrow S2 \;\;{\large \bf \times}\;\; S3 \longrightarrow H2$$
- **Self-Healing Alternate Path (Cost = 5):**
  $$H1 \longrightarrow S1 \longrightarrow S4 \longrightarrow S5 \longrightarrow S3 \longrightarrow H2$$

---

## 5. Empirical Benchmark Results

Running the baseline comparison (`python experiments/baseline.py`) produces the following verified results:

| Metric | Static Routing Baseline | Self-Healing SDN | Improvement |
| :--- | :--- | :--- | :--- |
| **Routing Mode** | Static (No Recovery) | Autonomous Dynamic Reroute | Dynamic Control Plane |
| **Packets Sent** | 146 | 138 | Equivalent Traffic Load |
| **Packets Delivered** | 43 | 125 | **+190.7% more packets delivered** |
| **Packets Lost** | 103 | 13 | **-87.4% fewer dropped packets** |
| **Packet Loss (%)** | **70.55 %** | **9.42 %** | **-61.13 percentage points** |
| **Packet Delivery Ratio (PDR)** | **29.45 %** | **90.58 %** | **+61.13 percentage points** |
| **Average End-to-End Delay** | 2.0000 time units | 2.3280 time units | Minor latency tradeoff (5 vs 4 hops) |
| **Throughput** | 11.74 kbps | 34.13 kbps | **2.9x higher sustained bandwidth** |
| **Detection Delay** | N/A (Unobserved) | 1.00 time units | Explicit heartbeat timeout |
| **Reroute Delay** | N/A (No Reroute) | 0.05 time units | Dijkstra execution + FlowMod |
| **Total Recovery Time (MTTR)**| $\infty$ (Failed / Never) | **1.05 time units** | Sub-interval restoration |

---

## 6. Repository Layout

```
intelligent-self-healing-sdn/
├── src/
│   ├── config.py                 # Centralized configuration dataclasses & paths
│   ├── topology/
│   │   ├── __init__.py
│   │   └── topology_manager.py   # NetworkX canonical 2-host 5-switch topology
│   ├── controller/
│   │   ├── __init__.py
│   │   └── sdn_controller.py     # Centralized SDN controller & flow table
│   ├── routing/
│   │   ├── __init__.py
│   │   └── dijkstra_router.py    # Dijkstra shortest path engine & validation
│   ├── simulation/
│   │   ├── __init__.py
│   │   ├── packet.py             # Packet dataclass with full lifecycle states
│   │   └── traffic_simulator.py  # Discrete-event SimPy traffic simulation
│   ├── failure/
│   │   ├── __init__.py
│   │   ├── failure_injector.py   # Scheduled link failure injection
│   │   └── failure_detector.py   # Heartbeat health monitoring & timeout logic
│   ├── recovery/
│   │   ├── __init__.py
│   │   └── recovery_engine.py    # Closed-loop recovery coordinator & MTTR
│   ├── metrics/
│   │   ├── __init__.py
│   │   └── metrics_collector.py  # PDR, loss %, throughput, and time series
│   └── analytics/
│       ├── __init__.py
│       └── analytics_engine.py   # Plotly interactive graphs & Matplotlib plots
├── dashboard/
│   └── app.py                    # Interactive Streamlit web application
├── experiments/
│   ├── run_experiment.py         # Standardized single/multi-trial runner
│   ├── baseline.py               # Static vs Self-Healing comparison script
│   └── batch_experiments.py      # Statistical scenario sweep (load, time, trials)
├── tests/
│   ├── test_topology.py          # Topology and link attribute unit tests
│   ├── test_routing.py           # Dijkstra calculation & invalidation tests
│   ├── test_simulation.py       # SimPy packet transit & delivery tests
│   ├── test_failure_recovery.py  # Closed-loop fault recovery tests
│   └── test_metrics.py           # KPI calculations & zero-division handling
├── docs/
│   ├── architecture.md           # Deep dive into system architecture & MAPE-K
│   ├── simulation_design.md      # SimPy discrete-event timing & state machine
│   ├── routing.md                # Dijkstra formulation & cost calculations
│   ├── failure_recovery.md       # Heartbeat detection & recovery lifecycle
│   ├── metrics.md                # Formal mathematical metric equations
│   ├── experiments.md            # Experimental protocol & benchmark tables
│   └── viva_questions.md         # Comprehensive viva voce defense Q&A
├── results/
│   ├── figures/                  # Publication-ready PNG comparison plots
│   └── metrics/                  # Output CSV benchmark records
├── main.py                       # Live CLI terminal demonstration
├── requirements.txt              # Production dependency specifications
└── README.md
```

---

## 7. Installation & Quickstart

### Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13
- Git

### Setup
```bash
# Clone the repository
git clone https://github.com/abhilash-velpula/intelligent-self-healing-sdn.git
cd intelligent-self-healing-sdn

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate    # Linux / macOS

# Install dependencies
pip install -r requirements.txt
```

---

## 8. Running the Project

### 1. Live Terminal Demonstration
Run the standard self-healing demonstration:
```bash
python main.py
```
To observe the static baseline failure mode (packet drops without recovery):
```bash
python main.py --mode static
```

### 2. Interactive Streamlit Dashboard
Launch the web interface:
```bash
streamlit run dashboard/app.py
```
Features available in the dashboard:
- Interactive 2D Plotly topology visualization.
- Sliders for simulation duration, traffic generation rate, fault injection time, and heartbeat interval.
- Side-by-side empirical Static vs Self-Healing benchmark comparison.
- Time-series throughput, loss, and PDR trajectory graphs.
- Real-time SDN controller event log and raw packet-level inspector with CSV download.

### 3. Run Comparative Baseline Script
```bash
python experiments/baseline.py
```
Saves `results/metrics/baseline_comparison.csv` and `results/figures/baseline_comparison.png`.

### 4. Run Multi-Trial Batch Experiments
```bash
python experiments/batch_experiments.py
```
Runs 8 experimental scenarios across parameter sweeps (normal operation, standard failure, static baseline, load sweep, fault timing sweep) and compiles summary statistics (mean, std, min, max) into `results/metrics/batch_experiments_summary.csv`.

### 5. Run the Automated Test Suite
```bash
pytest -v
```
Executes all 16 unit tests across topology, routing, simulation, failure recovery, and metrics modules.

---

## 9. Academic Limitations & Future Enhancements

### Limitations
1. **Simplified Switch Model:** Focuses on forwarding path programming; does not model TCAM flow table memory exhaustion or hardware switch CPU limits.
2. **Fixed Delay Model:** Links have deterministic traversal delays rather than dynamic M/M/1 queuing queue-overflow delays.
3. **Single Controller Instance:** Assumes a single centralized controller without distributed Raft clustering.

### Future Work
1. **Mininet / OpenFlow Integration:** Exporting computed forwarding paths as OpenFlow 1.3 `FlowMod` messages to real virtual switches in Mininet.
2. **Multi-Agent & QoS Routing:** Incorporating reinforcement learning (e.g. Q-learning) to dynamically optimize multi-criteria QoS routing under severe network congestion.

---

## 10. License
This project is open-source under the [MIT License](LICENSE).
