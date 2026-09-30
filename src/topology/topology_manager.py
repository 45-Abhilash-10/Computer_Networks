"""
topology_manager.py - Builds and manages NetworkX network topologies.

Implements the standard 2-Host, 5-Switch network topology with defined
primary and alternate paths, distinguishing between hosts and switches,
and tracking link properties (bandwidth, delay, cost, status).
"""

from typing import Dict, List, Optional, Tuple, Any
import networkx as nx


class TopologyManager:
    """Manages creation, state, and querying of the simulated SDN topology."""

    def __init__(self, default_bandwidth: float = 100.0, default_delay: float = 0.5):
        self.default_bandwidth = default_bandwidth
        self.default_delay = default_delay
        self.graph = nx.Graph()
        self._build_canonical_topology()

    def _build_canonical_topology(self) -> None:
        """
        Builds the canonical 2-Host, 5-Switch network topology.

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

        # Add Nodes with attributes
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

        # Add Edges with link parameters
        # (u, v, cost)
        edges = [
            ("H1", "S1", 1.0),
            ("S1", "S2", 1.0),
            ("S2", "S3", 1.0),  # Critical link for primary path
            ("S3", "H2", 1.0),
            ("S1", "S4", 1.0),
            ("S4", "S5", 1.0),
            ("S5", "S3", 1.0),
        ]

        for u, v, cost in edges:
            self.graph.add_edge(
                u,
                v,
                bandwidth=self.default_bandwidth,
                delay=self.default_delay,
                cost=cost,
                status="UP",
                capacity=1000,  # Max packets in queue/transit
            )

    def get_graph(self) -> nx.Graph:
        """Returns the full network graph."""
        return self.graph

    def get_active_graph(self) -> nx.Graph:
        """
        Returns a subgraph containing only active ('UP') links.
        Used by the routing engine to compute valid forwarding paths.
        """
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
        return [
            n for n, d in self.graph.nodes(data=True) if d.get("type") == "host"
        ]

    def get_switches(self) -> List[str]:
        """Returns list of all switch identifiers."""
        return [
            n for n, d in self.graph.nodes(data=True) if d.get("type") == "switch"
        ]

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
        """
        Returns clean, static 2D coordinates for rendering the topology.
        Ensures consistent presentation across Plotly and Matplotlib.
        """
        return {
            "H1": (-3.0, 0.0),
            "S1": (-1.5, 0.0),
            "S2": (0.0, 1.5),
            "S3": (1.5, 0.0),
            "S4": (-0.75, -1.5),
            "S5": (0.75, -1.5),
            "H2": (3.0, 0.0),
        }

    def reset_all_links(self) -> None:
        """Restores all links to 'UP' status."""
        for u, v in self.graph.edges():
            self.graph[u][v]["status"] = "UP"
