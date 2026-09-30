"""
topology_manager.py - Builds and manages static and dynamic NetworkX SDN topologies.

Supports:
1. Canonical 5-Switch Benchmark Topology (2 hosts, 5 switches)
2. Scalable Redundant Mesh Topology (arbitrary N switches with cross-links)
3. Multi-Tier Spine-Leaf Data Center Topology (spines, leaves, hosts)
4. Chordal Ring Topology (ring with cross-chords)
"""

from typing import Dict, List, Optional, Tuple, Any
import math
import networkx as nx


class TopologyManager:
    """Manages creation, state, and querying of simulated SDN topologies."""

    def __init__(
        self,
        default_bandwidth: float = 100.0,
        default_delay: float = 0.5,
        topology_type: str = "canonical",
        num_switches: int = 5,
    ):
        self.default_bandwidth = default_bandwidth
        self.default_delay = default_delay
        self.graph = nx.Graph()
        self.positions: Dict[str, Tuple[float, float]] = {}
        self.topology_type = topology_type.lower()
        self.num_switches = max(3, num_switches)

        self.build_topology(self.topology_type, self.num_switches)

    def build_topology(self, topology_type: str = "canonical", num_switches: int = 5) -> None:
        """Dispatches topology creation based on requested type."""
        self.topology_type = topology_type.lower()
        self.num_switches = max(3, num_switches)

        if self.topology_type == "spine_leaf":
            # e.g., 2 spines, remaining leaves
            num_spines = max(2, self.num_switches // 3)
            num_leaves = max(2, self.num_switches - num_spines)
            self._build_spine_leaf_topology(num_spines, num_leaves)
        elif self.topology_type == "mesh":
            self._build_mesh_topology(self.num_switches)
        elif self.topology_type == "ring":
            self._build_ring_topology(self.num_switches)
        else:
            self._build_canonical_topology()

    def _build_canonical_topology(self) -> None:
        """
        Builds the canonical 2-Host, 5-Switch benchmark network topology.

                     S2
                    /  \\
                   /    \\
        H1 —— S1        S3 —— H2
               \\        /
                \\      /
                 S4 —— S5

        Primary Path:   H1 -> S1 -> S2 -> S3 -> H2 (cost = 4)
        Alternate Path: H1 -> S1 -> S4 -> S5 -> S3 -> H2 (cost = 5)
        """
        self.graph.clear()
        self.positions.clear()

        nodes = [
            ("H1", {"type": "host", "label": "Host 1"}),
            ("H2", {"type": "host", "label": "Host 2"}),
            ("S1", {"type": "switch", "label": "Switch 1 (Ingress)"}),
            ("S2", {"type": "switch", "label": "Switch 2 (Primary Spine)"}),
            ("S3", {"type": "switch", "label": "Switch 3 (Egress)"}),
            ("S4", {"type": "switch", "label": "Switch 4 (Backup Ingress)"}),
            ("S5", {"type": "switch", "label": "Switch 5 (Backup Egress)"}),
        ]
        for node_id, attrs in nodes:
            self.graph.add_node(node_id, **attrs)

        edges = [
            ("H1", "S1", 1.0),
            ("S1", "S2", 1.0),
            ("S2", "S3", 1.0),
            ("S3", "H2", 1.0),
            ("S1", "S4", 1.0),
            ("S4", "S5", 1.0),
            ("S5", "S3", 1.0),
        ]
        for u, v, cost in edges:
            self._add_edge(u, v, cost)

        self.positions = {
            "H1": (-3.0, 0.0),
            "S1": (-1.5, 0.0),
            "S2": (0.0, 1.5),
            "S3": (1.5, 0.0),
            "S4": (-0.75, -1.5),
            "S5": (0.75, -1.5),
            "H2": (3.0, 0.0),
        }

    def _build_spine_leaf_topology(self, num_spines: int = 2, num_leaves: int = 4) -> None:
        """
        Builds a 2-Tier Clos Spine-Leaf data center fabric.
        Every leaf switch connects to every spine switch.
        Hosts connect to edge leaf switches.
        """
        self.graph.clear()
        self.positions.clear()

        # Add Spines
        spines = [f"SP{i+1}" for i in range(num_spines)]
        for i, sp in enumerate(spines):
            self.graph.add_node(sp, type="switch", label=f"Spine {i+1}")
            x = (i - (num_spines - 1) / 2) * 2.0
            self.positions[sp] = (x, 1.5)

        # Add Leaves
        leaves = [f"LF{j+1}" for j in range(num_leaves)]
        for j, lf in enumerate(leaves):
            self.graph.add_node(lf, type="switch", label=f"Leaf {j+1}")
            x = (j - (num_leaves - 1) / 2) * 1.5
            self.positions[lf] = (x, -0.2)

        # Interconnect each Leaf to every Spine
        for lf in leaves:
            for sp in spines:
                self._add_edge(lf, sp, cost=1.0)

        # Add End Hosts
        self.graph.add_node("H1", type="host", label="Host 1 (Ingress)")
        self.graph.add_node("H2", type="host", label="Host 2 (Egress)")
        self.positions["H1"] = (self.positions[leaves[0]][0] - 1.2, -1.6)
        self.positions["H2"] = (self.positions[leaves[-1]][0] + 1.2, -1.6)

        # Attach Hosts to edge leaf switches
        self._add_edge("H1", leaves[0], cost=1.0)
        self._add_edge("H2", leaves[-1], cost=1.0)

    def _build_mesh_topology(self, num_switches: int = 8) -> None:
        """
        Builds a redundant mesh topology with N switches and multiple cross-links.
        Guarantees biconnectivity so alternate routes always exist upon link failure.
        """
        self.graph.clear()
        self.positions.clear()

        switches = [f"S{i+1}" for i in range(num_switches)]
        for i, sw in enumerate(switches):
            self.graph.add_node(sw, type="switch", label=f"Switch {i+1}")

        # Connect primary backbone chain S1 -> S2 -> ... -> S_N
        for i in range(num_switches - 1):
            self._add_edge(switches[i], switches[i + 1], cost=1.0)

        # Connect redundant chords (e.g. i to i+2, and 0 to N-1)
        for i in range(num_switches - 2):
            self._add_edge(switches[i], switches[i + 2], cost=1.5)

        if num_switches >= 4:
            self._add_edge(switches[0], switches[-1], cost=2.0)
            self._add_edge(switches[1], switches[-2], cost=1.8)

        # End hosts
        self.graph.add_node("H1", type="host", label="Host 1")
        self.graph.add_node("H2", type="host", label="Host 2")
        self._add_edge("H1", switches[0], cost=1.0)
        self._add_edge("H2", switches[-1], cost=1.0)

        # Layout positions in 2 rows or circle
        radius = 2.0
        for i, sw in enumerate(switches):
            angle = math.pi * (1.0 - (i / max(1, num_switches - 1)))
            x = math.cos(angle) * radius * 1.3
            y = math.sin(angle) * (radius if i % 2 == 1 else -radius * 0.7)
            self.positions[sw] = (round(x, 2), round(y, 2))

        self.positions["H1"] = (-3.2, 0.0)
        self.positions["H2"] = (3.2, 0.0)

    def _build_ring_topology(self, num_switches: int = 8) -> None:
        """
        Builds a chordal ring topology (closed ring with diametric cross-links).
        """
        self.graph.clear()
        self.positions.clear()

        switches = [f"S{i+1}" for i in range(num_switches)]
        for i, sw in enumerate(switches):
            self.graph.add_node(sw, type="switch", label=f"Switch {i+1}")

        # Connect ring
        for i in range(num_switches):
            self._add_edge(switches[i], switches[(i + 1) % num_switches], cost=1.0)

        # Cross chords
        for i in range(num_switches // 2):
            opposite = (i + num_switches // 2) % num_switches
            self._add_edge(switches[i], switches[opposite], cost=1.5)

        # End hosts attached to opposite ends of ring
        self.graph.add_node("H1", type="host", label="Host 1")
        self.graph.add_node("H2", type="host", label="Host 2")
        self._add_edge("H1", switches[0], cost=1.0)
        self._add_edge("H2", switches[num_switches // 2], cost=1.0)

        # Circular positions
        radius = 2.0
        for i, sw in enumerate(switches):
            angle = (2 * math.pi * i) / num_switches
            x = round(radius * math.cos(angle), 2)
            y = round(radius * math.sin(angle), 2)
            self.positions[sw] = (x, y)

        self.positions["H1"] = (self.positions[switches[0]][0] - 1.2, self.positions[switches[0]][1])
        opp = switches[num_switches // 2]
        self.positions["H2"] = (self.positions[opp][0] + 1.2, self.positions[opp][1])

    def _add_edge(self, u: str, v: str, cost: float = 1.0) -> None:
        """Adds an edge with standard SDN parameters."""
        self.graph.add_edge(
            u,
            v,
            bandwidth=self.default_bandwidth,
            delay=self.default_delay,
            cost=cost,
            status="UP",
            capacity=1000,
        )

    def get_graph(self) -> nx.Graph:
        """Returns the full network graph."""
        return self.graph

    def get_active_graph(self) -> nx.Graph:
        """Returns subgraph containing only active ('UP') links."""
        active_edges = [
            (u, v, data)
            for u, v, data in self.graph.edges(data=True)
            if data.get("status") == "UP"
        ]
        active_subgraph = nx.Graph()
        for node, data in self.graph.nodes(data=True):
            active_subgraph.add_node(node, **data)
        for u, v, data in active_edges:
            active_subgraph.add_edge(u, v, **data)
        return active_subgraph

    def get_hosts(self) -> List[str]:
        """Returns list of all host identifiers."""
        return [n for n, d in self.graph.nodes(data=True) if d.get("type") == "host"]

    def get_switches(self) -> List[str]:
        """Returns list of all switch identifiers."""
        return [n for n, d in self.graph.nodes(data=True) if d.get("type") == "switch"]

    def get_link_status(self, u: str, v: str) -> str:
        """Returns the status ('UP' or 'DOWN') of link (u, v)."""
        if self.graph.has_edge(u, v):
            return self.graph[u][v].get("status", "UNKNOWN")
        raise ValueError(f"Link ({u}, {v}) does not exist in topology.")

    def set_link_status(self, u: str, v: str, status: str) -> None:
        """Sets link status ('UP' or 'DOWN')."""
        if not self.graph.has_edge(u, v):
            raise ValueError(f"Link ({u}, {v}) does not exist in topology.")
        status = status.upper()
        if status not in ("UP", "DOWN"):
            raise ValueError(f"Invalid status '{status}'. Must be 'UP' or 'DOWN'.")
        self.graph[u][v]["status"] = status

    def get_all_links(self) -> List[Tuple[str, str, Dict[str, Any]]]:
        """Returns list of all links with their attributes."""
        return list(self.graph.edges(data=True))

    def get_node_positions(self) -> Dict[str, Tuple[float, float]]:
        """Returns 2D coordinates for rendering the topology in Plotly."""
        if not self.positions:
            # Fallback to spring layout
            pos = nx.spring_layout(self.graph, seed=42)
            self.positions = {n: (float(x) * 3.0, float(y) * 2.0) for n, (x, y) in pos.items()}
        return self.positions

    def reset_all_links(self) -> None:
        """Restores all links to 'UP' status."""
        for u, v in self.graph.edges():
            self.graph[u][v]["status"] = "UP"
