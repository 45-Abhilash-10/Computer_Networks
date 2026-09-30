# System Architecture: Intelligent Self-Healing SDN Network

## 1. High-Level Overview
This project models an **SDN (Software-Defined Networking) control-plane software simulation** in Python. It demonstrates how centralizing network control intelligence enables automated fault detection, dynamic topology updates, alternate shortest-path calculation, and seamless packet traffic rerouting without manual human operator intervention.

---

## 2. Technical Positioning
- **Software Simulation:** Implemented in pure Python using `NetworkX` for graph-based network topology state and `SimPy` for discrete-event packet forwarding.
- **Academic Distinction:** This is **not** a hardware or physical OpenFlow/Mininet deployment. Instead, it faithfully simulates the core algorithmic and architectural principles of the SDN paradigm:
  1. Separation of the Control Plane from the Data Plane.
  2. Centralized global topology visibility.
  3. Dynamic programming of flow forwarding tables.
  4. Explicit closed-loop fault monitoring and self-healing.

---

## 3. The MAPE-K Autonomic Architecture
The architecture is structured around the classic **MAPE-K** (Monitor, Analyze, Plan, Execute, Knowledge) closed-loop autonomic management pattern:

```
  +-------------------------------------------------------------+
  |                        SDN CONTROLLER                       |
  |                                                             |
  |   +-----------------------------------------------------+   |
  |   |             Global Topology Knowledge Base          |   |
  |   |       (NetworkX Graph with Link Attributes)         |   |
  |   +-----------------------------------------------------+   |
  |                              |                              |
  |             +----------------+----------------+             |
  |             |                                 |             |
  |             v                                 v             |
  |   +-------------------+             +-------------------+   |
  |   |  Routing Engine   |             |   Flow Table      |   |
  |   | (Dijkstra Router) |             |  (Forwarding)     |   |
  |   +-------------------+             +-------------------+   |
  +-------------------------------------------------------------+
         ^                                             |
         | Heartbeat Notification                      | FlowMod Installation
         |                                             v
  +-------------------+                         +---------------+
  | Failure Detector  |                         |  Data Plane   |
  | (Heartbeat Probe) |                         | (Packet Flow) |
  +-------------------+                         +---------------+
         ^                                             |
         | Link Health Polling                         | Packet Forwarding
         +----------------------+----------------------+
                                |
                    +-----------------------+
                    |  Simulated Physical   |
                    |   Topology Fabric     |
                    +-----------------------+
```

### Component Breakdown

1. **Topology Manager (`src/topology/topology_manager.py`)**:
   - Manages the underlying graph $G = (V, E)$.
   - Distinguishes between End Hosts ($H1, H2$) and SDN Switches ($S1, S2, S3, S4, S5$).
   - Maintains physical edge attributes: `bandwidth`, `delay`, `cost`, and operational `status` (`UP` vs `DOWN`).
   - Produces the active subgraph containing only operational links for the routing engine.

2. **SDN Controller (`src/controller/sdn_controller.py`)**:
   - Central control point for the simulated network.
   - Discovers topology and maintains the flow table mapping $(src, dst) \to route$.
   - Supports two operational modes:
     - `self_healing`: Invalidates stale paths upon failure notification and dynamically computes alternate paths.
     - `static`: Simulates legacy/static behavior where broken paths are retained, inducing continuous packet loss.
   - Logs timestamped control-plane events for auditing and analysis.

3. **Dijkstra Routing Engine (`src/routing/dijkstra_router.py`)**:
   - Calculates the minimum-cost path between endpoints using Dijkstra's algorithm.
   - Computes path hop counts, cumulative delays, and metric costs.
   - Validates whether an existing route is structurally intact across the active graph.

4. **Failure Injection & Detection (`src/failure/`)**:
   - **Failure Injector (`failure_injector.py`):** Physically severs targeted links at scheduled simulation timestamps.
   - **Failure Detector (`failure_detector.py`):** Simulates periodic switch health polling (heartbeats). It explicitly quantifies the detection delay between physical failure inception and controller notification.

5. **Recovery Engine (`src/recovery/recovery_engine.py`)**:
   - Coordinates the autonomous self-healing sequence.
   - Records the exact timestamps for failure injection, detection, reroute execution, and total MTTR (Mean Time to Recovery).

6. **Traffic Simulator (`src/simulation/traffic_simulator.py`)**:
   - Discrete-event simulation powered by SimPy.
   - Generates packets at end hosts, simulates transmission and propagation latencies hop-by-hop, drops packets that encounter broken links, and reroutes flows once the controller installs new forwarding rules.

7. **Metrics Collector (`src/metrics/metrics_collector.py`)**:
   - Computes packet loss percentage, Packet Delivery Ratio (PDR), latency distributions, throughput (kbps and pps), and temporal time-series aggregations.
