# Key Performance Indicators & Metrics Definitions

## 1. Primary Experimental Metrics

All performance evaluations in this project rely on formally defined networking and recovery metrics:

### 1. Packet Loss Percentage
$$\text{Packet Loss } (\%) = \left(\frac{N_{lost}}{N_{sent}}\right) \times 100$$
- $N_{sent}$: Total packets generated at source host $H1$.
- $N_{lost}$: Total packets dropped during transit due to severed links or missing routes.

### 2. Packet Delivery Ratio (PDR)
$$\text{PDR } (\%) = \left(\frac{N_{delivered}}{N_{sent}}\right) \times 100$$
- $N_{delivered}$: Total packets successfully received at destination host $H2$ (including both primary and rerouted deliveries).
- Note: $\text{PDR } (\%) + \text{Packet Loss } (\%) = 100\%$.

### 3. Average End-to-End Delay
$$\bar{D} = \frac{1}{N_{delivered}} \sum_{i=1}^{N_{delivered}} (t_{receive, i} - t_{send, i})$$
- Measures the mean propagation and transmission latency for all successfully delivered packets.
- In our canonical topology:
  - Primary path (4 hops) has delay $\approx 2.0$ units.
  - Alternate path (5 hops) has delay $\approx 2.5$ units.

### 4. Data Throughput
$$\text{Throughput (kbps)} = \frac{N_{delivered} \times \text{Packet Size (Bytes)} \times 8}{T_{simulation} \times 1000}$$
- Quantifies the actual bandwidth sustained across the entire simulation duration.

### 5. Detection Delay ($\Delta t_{detect}$)
$$\Delta t_{detect} = t_{detect} - t_{fail}$$
- Measures the latency between physical link disruption and controller notification by the heartbeat monitor.

### 6. Reroute Delay ($\Delta t_{reroute}$)
$$\Delta t_{reroute} = t_{reroute} - t_{detect}$$
- Measures the time taken by the controller to compute the alternate Dijkstra path and update switch forwarding tables.

### 7. Total Recovery Time (MTTR)
$$\text{Recovery Time} = t_{reroute} - t_{fail} = \Delta t_{detect} + \Delta t_{reroute}$$
- Represents the total duration during which the network path was down or impaired.

---

## 2. Temporal Time-Series Metrics
To evaluate dynamic network response, the metrics collector partitions simulation time into discrete interval bins $\Delta B$ (default: 1.0 unit):
- **Delivered Packets per Bin:** Throughput trajectory before, during, and after failure.
- **Dropped Packets per Bin:** Transient drop spike during the detection window $[t_{fail}, t_{detect}]$.
- **Interval PDR (%):** Visualizes the sharp dip to 0% during the failure window and rapid recovery to 100% post-rerouting.
