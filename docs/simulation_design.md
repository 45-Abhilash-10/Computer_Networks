# Simulation Design: Discrete-Event Modeling with SimPy

## 1. Discrete-Event Simulation Fundamentals
In a physical network, packet transmission and switch processing happen continuously in real time. In this project, packet behaviors and control-plane actions are modeled using **SimPy**, a process-based discrete-event simulation framework.

### Discrete Simulation Time Units
Simulation time does not advance continuously; instead, the clock jumps from one scheduled event to the next.
- **Time Unit:** Simulation time is expressed in normalized **discrete simulation time units** (e.g., 1 time unit $\approx$ 1 second or 100 milliseconds in a real network).
- **Packet Delays:** Each link traversal advances the clock by `link_delay` units (default: 0.5 units).
- **Traffic Rate:** Configured as `packet_rate` packets generated per unit time (e.g., 5.0 packets/unit $\implies$ inter-arrival time $\Delta t = 1.0 / 5.0 = 0.2$ units).

---

## 2. Packet Lifecycle State Machine

A simulated packet undergoes the following transitions:

```
    [GENERATED]
         |
         v
    [IN_TRANSIT] ──── Link Broken ────> [DROPPED] (Recorded with Drop Reason)
         |
    Link Healthy & Reached Target
         v
    [DELIVERED] / [REROUTED]
```

### State Definitions
1. **`GENERATED`**: Instantiated at the source host ($H1$) with timestamp $t_{gen}$.
2. **`IN_TRANSIT`**: Assigned an active forwarding route by the SDN controller; traversing intermediate switch nodes hop-by-hop.
3. **`DROPPED`**: Encountered a severed link (`status == "DOWN"`) along its designated path. Drop reason and drop node are recorded.
4. **`DELIVERED`**: Successfully reached destination ($H2$) along the primary path. Latency $D = t_{delivery} - t_{gen}$.
5. **`REROUTED`**: Successfully reached destination ($H2$) after being forwarded along the alternate self-healing route.

---

## 3. Concurrent SimPy Simulation Processes

The simulation executes three primary concurrent processes inside the `simpy.Environment`:

1. **Traffic Generator Process (`_traffic_generator_process`)**:
   - Loops from $t = 0.0$ to $t = \text{duration}$.
   - Spawns a packet every $\Delta t = 1 / \text{rate}$ time units.
   - Launches an independent `_packet_transit_process` for each packet.

2. **Packet Transit Process (`_packet_transit_process`)**:
   - Queries the SDN controller for the current forwarding route: `controller.get_route(src, dst)`.
   - Iterates through each link $(u, v)$ in the route:
     - Verifies physical link state. If `DOWN`, packet drops immediately.
     - Yields `env.timeout(link_delay)` to simulate transit time.
     - Re-checks link state upon arrival at $v$. If the link broke while the packet was in flight, drops with `IN_TRANSIT_LINK_FAILURE`.
   - Upon reaching destination, marks delivered and notifies metrics collector.

3. **Fault Injection Process (`_failure_injector_process`)**:
   - Yields `env.timeout(failure_time)`.
   - Severely marks the target link $(S2, S3)$ as `DOWN` in physical topology.
   - Logs `FAILURE_INJECTED` timestamp.

4. **Heartbeat Polling Process (`_heartbeat_process`)**:
   - Loops indefinitely with `yield env.timeout(heartbeat_interval)`.
   - Probes link health. When a link is unresponsive and the timeout has elapsed, triggers the recovery engine.
