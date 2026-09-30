# Fault Injection, Explicit Detection, and Self-Healing Recovery

## 1. The Autonomous Self-Healing Lifecycle

A self-healing network must execute four distinct stages:
$$\text{Observe} \longrightarrow \text{Detect} \longrightarrow \text{Decide} \longrightarrow \text{Recover}$$

```
t = 0.0          t = 10.0                 t = 11.0                     t = 11.05
  |                 |                        |                            |
  +-----------------+------------------------+----------------------------+
  Normal Flow    Link Cut                 Heartbeat Timeout            Alternate Route
  (H1-S1-S2-S3-H2) (Physical Failure)      Controller Notified          Installed & Traffic Resumes
                    |<-- Detection Delay --->|<-- Reroute Delay -->|
                    |<---------------- Total Recovery Time ---------------------->|
```

---

## 2. Explicit Failure Detection Mechanism
In naive network simulations, the controller instantaneously "knows" a link has failed at the exact microsecond of the cut. In real networking, this is impossible—the control plane is physically separated from data plane switches and relies on monitoring signals.

This simulation models **explicit failure detection**:
1. **Heartbeat Polling:** An asynchronous probe process runs every $\tau_{heartbeat}$ units (default: 1.0 unit).
2. **Timeout Condition:** When a physical link is severed at $t_{fail}$, the monitor requires waiting until the next heartbeat probe cycle confirms the missing echo response:
   $$t_{detect} \ge t_{fail} + \tau_{heartbeat}$$
3. **Detection Delay Metric:**
   $$\Delta t_{detect} = t_{detect} - t_{fail}$$

---

## 3. The Rerouting and Recovery Phase
Once the failure notification reaches the SDN Controller:
1. **Topology Update:** Link $(S2, S3)$ status set to `DOWN`.
2. **Flow Inspection:** The controller scans all active flow entries in its flow table.
3. **Route Invalidation:** Flows containing $(S2, S3)$ are invalidated:
   $$\text{Route Invalidated: } H1 \to S1 \to S2 \to S3 \to H2$$
4. **Dijkstra Recomputation:** Shortest path is recalculated over the active subgraph:
   $$\text{New Route: } H1 \to S1 \to S4 \to S5 \to S3 \to H2$$
5. **FlowMod Installation:** New forwarding rules are installed into the switches.
6. **Reroute Delay Metric:**
   $$\Delta t_{reroute} = t_{installed} - t_{detect}$$
7. **Total Recovery Time (MTTR):**
   $$\text{Recovery Time} = t_{installed} - t_{fail} = \Delta t_{detect} + \Delta t_{reroute}$$

---

## 4. Why Self-Healing Is "Intelligent"
The system is called "intelligent" because it implements **autonomous closed-loop feedback**:
- It senses the data-plane health.
- It detects anomaly conditions without operator prompts.
- It reasons over the global graph topology to locate valid alternate paths.
- It actuates forwarding changes safely without human keyboard interaction.
- It does **not** rely on artificial machine learning hype to claim intelligence; the intelligence is structural and algorithmic.
