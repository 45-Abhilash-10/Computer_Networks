"""
dijkstra_router.py - Routing engine using Dijkstra's shortest path algorithm.

Calculates shortest paths on active network topology graphs using NetworkX,
validates existing paths against current link states, and computes alternate routes.
"""

from typing import List, Optional, Tuple, Dict, Any
import networkx as nx


class RoutingError(Exception):
    """Base exception for routing failures."""
    pass


class NoPathError(RoutingError):
    """Raised when no valid path exists between source and destination."""
    pass


class DijkstraRouter:
    """Computes and validates network routes using Dijkstra's shortest path algorithm."""

    def __init__(self, weight_attribute: str = "cost"):
        """
        Args:
            weight_attribute: Edge attribute key to minimize ('cost', 'delay', etc.).
        """
        self.weight_attribute = weight_attribute

    def calculate_route(
        self, graph: nx.Graph, source: str, destination: str
    ) -> List[str]:
        """
        Calculates the shortest path from source to destination on the provided graph.

        Args:
            graph: The network topology (typically an active subgraph).
            source: Source node ID (e.g. 'H1').
            destination: Destination node ID (e.g. 'H2').

        Returns:
            List of node IDs representing the ordered path.

        Raises:
            NoPathError: If no path exists between source and destination.
            ValueError: If source or destination not in graph.
        """
        if source not in graph:
            raise ValueError(f"Source node '{source}' not present in topology.")
        if destination not in graph:
            raise ValueError(f"Destination node '{destination}' not present in topology.")

        try:
            path = nx.shortest_path(
                graph,
                source=source,
                target=destination,
                weight=self.weight_attribute,
                method="dijkstra",
            )
            return list(path)
        except nx.NetworkXNoPath:
            raise NoPathError(
                f"No active path exists between '{source}' and '{destination}'."
            )

    def is_route_valid(self, graph: nx.Graph, route: List[str]) -> bool:
        """
        Checks whether all consecutive hops in the given route exist as active ('UP')
        links in the provided graph.

        Args:
            graph: The network graph to test against.
            route: Ordered list of nodes.

        Returns:
            True if all links exist and are 'UP', False otherwise.
        """
        if not route or len(route) < 2:
            return False

        for i in range(len(route) - 1):
            u, v = route[i], route[i + 1]
            if not graph.has_edge(u, v):
                return False
            status = graph[u][v].get("status", "UP")
            if status != "UP":
                return False
        return True

    def get_route_details(
        self, graph: nx.Graph, route: List[str]
    ) -> Dict[str, Any]:
        """
        Computes path summary statistics (hop count, total delay, total cost).

        Args:
            graph: The network graph containing edge attributes.
            route: Ordered list of nodes.

        Returns:
            Dictionary with hop_count, total_cost, total_delay, links.
        """
        if not route or len(route) < 2:
            return {"hop_count": 0, "total_cost": 0.0, "total_delay": 0.0, "links": []}

        total_cost = 0.0
        total_delay = 0.0
        links = []

        for i in range(len(route) - 1):
            u, v = route[i], route[i + 1]
            if graph.has_edge(u, v):
                edge_data = graph[u][v]
                total_cost += edge_data.get("cost", 1.0)
                total_delay += edge_data.get("delay", 0.5)
                links.append((u, v))
            else:
                links.append((u, v))

        return {
            "hop_count": len(route) - 1,
            "total_cost": total_cost,
            "total_delay": total_delay,
            "links": links,
        }
