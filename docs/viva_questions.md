# Comprehensive Viva & Technical Defense Guide

This guide prepares you for questions from external examiners, guides, and faculty panels regarding your major project: **Intelligent Self-Healing SDN Network**.

---

### Q1: What is Software-Defined Networking (SDN)?
**Answer:** SDN is a network architecture paradigm that decouples the **Control Plane** (which decides how traffic should be routed) from the **Data Plane** (the physical or virtual switches that actually forward packets based on rules). By logically centralizing control intelligence into a programmable software controller, network operators can dynamically reconfigure forwarding behavior across the entire network via software.

---

### Q2: What is the Control Plane vs Data Plane in your project?
**Answer:**
- **Control Plane (`src/controller/sdn_controller.py`):** Maintains the global network topology graph (using NetworkX), queries link states, runs Dijkstra's algorithm to compute shortest paths, and installs/updates forwarding entries in flow tables.
- **Data Plane (`src/simulation/traffic_simulator.py`):** Represents the switches and end-hosts transmitting packets. It receives forwarding paths from the controller, simulates link transit delays, and drops packets if an assigned physical link is down.

---

### Q3: Why is SDN uniquely suited for failure recovery?
**Answer:** In traditional distributed routing (OSPF, RIP, BGP), each router must discover a fault independently, generate Link-State Advertisements (LSAs), flood them across the entire network, and wait for all routers to independently converge. This process can take seconds to minutes, causing routing loops and blackholes. In SDN, a centralized controller has global topology visibility; the moment it detects a fault, it computes an alternate loop-free route centrally and installs it immediately into the relevant switches.

---

### Q4: Why did you use NetworkX?
**Answer:** NetworkX is the industry-standard Python graph analytics library. It allows us to represent the network topology as an undirected graph $G = (V, E)$ where nodes represent switches/hosts and edges carry physical link parameters (`bandwidth`, `delay`, `cost`, `status`). It also provides an optimized, mathematically verified implementation of Dijkstra's algorithm.

---

### Q5: Why did you use SimPy?
**Answer:** SimPy is a process-oriented discrete-event simulation framework. Network packet forwarding is inherently event-driven: packet generation, transmission delay, queue wait time, link cuts, and heartbeat probe timers are all discrete temporal events. SimPy provides a deterministic event scheduler that lets us accurately model packets moving hop-by-hop across links without resorting to imprecise sleep timers.

---

### Q6: Why Dijkstra's algorithm and not Machine Learning for routing?
**Answer:** Dijkstra is mathematically guaranteed to find the provably optimal shortest path in $O(|E| + |V| \log |V|)$ time without training overhead, convergence instability, or hallucinated loops. While ML can predict traffic congestion, core route computation in production networking must be deterministic, loop-free, and mathematically verifiable.

---

### Q7: What exact sequence of events happens when a link fails?
**Answer:**
1. **Physical Disruption (t = 10.0):** Link $S2-S3$ is severed in the physical data plane.
2. **Packet Drops:** Packets currently in transit or sent on the old path encounter the severed link and are dropped.
3. **Heartbeat Timeout (t = 11.0):** The periodic health monitor detects a missing response on $S2-S3$ and notifies the controller.
4. **Topology Graph Update:** Controller marks $S2-S3$ as `DOWN` and removes it from the active graph.
5. **Route Invalidation:** Controller marks flow $H1 \to S1 \to S2 \to S3 \to H2$ as invalid.
6. **Dijkstra Recomputation:** Shortest path is recalculated on the active graph, yielding $H1 \to S1 \to S4 \to S5 \to S3 \to H2$.
7. **Flow Installation & Rerouting (t = 11.05):** New flow rules are installed; subsequent packets use the alternate path and are delivered successfully.

---

### Q8: How is failure detected? Why is detection delayed?
**Answer:** Failure is detected using a simulated **heartbeat / probe mechanism** running at a configurable interval (default: 1.0 unit). In real networks, controllers cannot instantly know a fiber was cut until a keep-alive probe fails to return. Modeling an explicit detection interval ensures our recovery benchmarks accurately reflect real-world monitoring latency ($\Delta t_{detect} = t_{detect} - t_{fail}$).

---

### Q9: What makes this project "Intelligent"?
**Answer:** The project is intelligent because it implements an **autonomic closed-loop feedback cycle** (MAPE-K: Monitor $\to$ Analyze $\to$ Plan $\to$ Execute). It autonomously senses data-plane degradation, detects the fault, computes an alternate path, and heals the network without human operator intervention. We emphasize architectural intelligence rather than artificial machine learning buzzwords.

---

### Q10: How are the key metrics calculated?
**Answer:**
- **Packet Loss %:** $\frac{\text{Packets Dropped}}{\text{Packets Sent}} \times 100$
- **Packet Delivery Ratio (PDR %):** $\frac{\text{Packets Delivered}}{\text{Packets Sent}} \times 100$
- **Average Delay:** Mean duration from creation time to delivery time across all received packets.
- **Throughput:** Total bits delivered divided by total simulation duration.
- **Recovery Time:** Duration from physical failure inception to new route installation ($t_{reroute} - t_{fail}$).

---

### Q11: Why is the Static Routing baseline comparison essential?
**Answer:** A scientific project requires a control baseline. By running an identical simulation in **Static Mode** (where the controller does not adapt), we prove empirically that static routing suffers **70.55% packet loss** when a core link fails, whereas Self-Healing SDN limits loss to **9.42%** during the brief transient detection window, restoring delivery to 100%.

---

### Q12: Why is this not a real OpenFlow / Mininet deployment?
**Answer:** We position this project honestly as an **SDN control-plane software simulation**. Emulators like Mininet require Linux kernel network namespaces and root privileges, making cross-platform execution, automated testing, and statistical parameter sweeps significantly more complex. Simulating the control plane in Python with SimPy allows us to rigorously evaluate the fundamental algorithmic and architectural trade-offs of self-healing with complete transparency and repeatability.

---

### Q13: What are the primary limitations of this simulation?
**Answer:**
1. **Simplified Switch Hardware:** We do not model hardware TCAM memory constraints or switch CPU exhaustion.
2. **Uniform Queueing:** Link delays are modeled as fixed propagation delays without dynamic M/M/1 queuing buffer overflow.
3. **Single Controller:** We assume a single centralized controller without distributed Raft consensus or controller failover.

---

### Q14: What is the research contribution of this project?
**Answer:** The contribution is an **integrated, reproducible, modular experimental framework** that combines discrete-event traffic generation, explicit heartbeat fault detection, dynamic Dijkstra recalculation, quantitative recovery benchmarking, and interactive visual analytics in an accessible, open-source Python codebase.
