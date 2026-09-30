# Routing Engine: Dijkstra's Shortest Path Algorithm in SDN

## 1. Dijkstra Routing Principles in SDN
In traditional IP routing (such as OSPF or IS-IS), every router runs its own independent instance of Dijkstra's algorithm based on Link State Advertisements (LSAs) flooded across the network. 

In a Software-Defined Network:
1. The **SDN Controller** maintains a centralized, globally synchronized view of the network graph $G = (V, E)$.
2. When a path is needed, the controller runs Dijkstra centrally across the **active subgraph** $G_{active} \subseteq G$.
3. The computed path is installed directly into switch flow tables as forwarding rules.

---

## 2. Canonical Topology Formulation

```
             S2 (Cost=1)
            /  \
           /    \
H1 —— S1        S3 —— H2
       \        /
        \      /
         S4 —— S5 (Cost=1 each)
```

- **Nodes:** $V = \{H1, H2, S1, S2, S3, S4, S5\}$
- **Edges & Metric Weights:**
  - $(H1, S1): 1$
  - $(S1, S2): 1$
  - $(S2, S3): 1$
  - $(S3, H2): 1$
  - $(S1, S4): 1$
  - $(S4, S5): 1$
  - $(S5, S3): 1$

### Primary Path Calculation
Under normal, healthy conditions ($all\ links = UP$):
- Path A: $H1 \to S1 \to S2 \to S3 \to H2 \implies \text{Total Cost} = 1 + 1 + 1 + 1 = 4$
- Path B: $H1 \to S1 \to S4 \to S5 \to S3 \to H2 \implies \text{Total Cost} = 1 + 1 + 1 + 1 + 1 = 5$

Dijkstra evaluates $\min(\text{Cost})$, naturally selecting **Path A** as the primary forwarding path.

### Alternate Path Calculation Post-Failure
When link $(S2, S3)$ is cut:
- Link $(S2, S3)$ is marked `DOWN` and omitted from the active graph $G_{active}$.
- Path A becomes broken and structurally impossible.
- Dijkstra automatically re-evaluates the active graph and converges on **Path B**:
  $$H1 \to S1 \to S4 \to S5 \to S3 \to H2$$
- The alternate path is **never hardcoded**; it is the mathematical outcome of running Dijkstra over the updated graph.

---

## 3. Route Invalidation & Verification
The router provides explicit route validation via `is_route_valid(graph, route)`.
A route is valid if and only if for every consecutive node pair $(u_i, u_{i+1})$ in the route:
1. Edge $(u_i, u_{i+1})$ exists in the graph.
2. The operational status of the edge is `UP`.

If any link in the sequence fails, the controller immediately flags the route as `INVALID` and purges the stale flow entry.
