"""
sdn_controller.py - Centralized SDN Controller abstraction for software simulation.

Maintains the global network topology, handles flow installation, processes
failure notifications, updates topology graphs, and triggers dynamic route
recomputation (in self-healing mode) or preserves stale routes (in static mode).
"""

from typing import Dict, List, Optional, Tuple, Any
import networkx as nx
from src.topology.topology_manager import TopologyManager
from src.routing.dijkstra_router import DijkstraRouter, NoPathError


class SDNController:
    """
    Simulated Centralized SDN Controller.

    Represents the SDN Control Plane:
    - Maintains a global view of the network topology
    - Programs flow paths (forwarding tables)
    - Receives telemetry and fault notifications
    - Executes route computation and invalidation
    """

    def __init__(
        self,
        topology_manager: Optional[TopologyManager] = None,
        router: Optional[DijkstraRouter] = None,
        routing_mode: str = "self_healing",
    ):
        """
        Args:
            topology_manager: TopologyManager instance providing network state.
            router: DijkstraRouter instance for path calculations.
            routing_mode: 'self_healing' (dynamic rerouting) or 'static' (no recovery).
        """
        self.topology_manager = topology_manager or TopologyManager()
        self.router = router or DijkstraRouter()
        self.routing_mode = routing_mode.lower()
        self.controller_computation_delay = 0.05

        # Flow table: maps (src, dst) -> List[str] representing ordered node path
        self.flow_table: Dict[Tuple[str, str], List[str]] = {}

        # Log of controller actions
        self.event_log: List[Dict[str, Any]] = []

        # Initialize topology discovery
        self.discover_topology()

    def log_event(self, timestamp: float, event_type: str, details: str) -> None:
        """Appends a structured event to the controller's internal log."""
        entry = {
            "timestamp": round(timestamp, 2),
            "event_type": event_type,
            "details": details,
        }
        self.event_log.append(entry)

    def discover_topology(self) -> nx.Graph:
        """
        Queries and updates controller's internal topology graph.
        Simulates OpenFlow/LLDP topology discovery.
        """
        graph = self.topology_manager.get_active_graph()
        self.log_event(0.0, "TOPOLOGY_DISCOVERY", f"Discovered {len(graph.nodes)} nodes and {len(graph.edges)} active links.")
        return graph

    def get_route(self, source: str, destination: str) -> Optional[List[str]]:
        """
        Returns the installed route for a flow, or computes and installs a new one.
        """
        key = (source, destination)
        if key in self.flow_table:
            return list(self.flow_table[key])

        # If not installed, compute initial route
        active_graph = self.topology_manager.get_active_graph()
        try:
            route = self.router.calculate_route(active_graph, source, destination)
            self.install_route(source, destination, route, timestamp=0.0)
            return list(route)
        except NoPathError:
            self.log_event(0.0, "ROUTE_ERROR", f"No path available from {source} to {destination}.")
            return None

    def install_route(
        self, source: str, destination: str, route: List[str], timestamp: float = 0.0
    ) -> None:
        """
        Installs an active forwarding rule for the flow (source -> destination).
        Simulates pushing OpenFlow FlowMod messages.
        """
        key = (source, destination)
        self.flow_table[key] = list(route)
        path_str = " -> ".join(route)
        self.log_event(timestamp, "FLOW_INSTALL", f"Flow [{source}->{destination}] installed: {path_str}")

    def is_route_affected_by_failure(
        self, route: List[str], failed_u: str, failed_v: str
    ) -> bool:
        """Checks if a given route contains the failed link in either direction."""
        if not route or len(route) < 2:
            return False
        for i in range(len(route) - 1):
            u, v = route[i], route[i + 1]
            if (u == failed_u and v == failed_v) or (u == failed_v and v == failed_u):
                return True
        return False

    def handle_failure_notification(
        self, u: str, v: str, detection_time: float
    ) -> Dict[str, Any]:
        """
        Called when a failure detector explicitly notifies the controller of a link failure.

        If routing_mode == 'self_healing':
            1. Updates topology graph (marks link DOWN)
            2. Identifies affected flows
            3. Invalidates affected paths
            4. Recomputes alternate shortest paths using active topology
            5. Installs new forwarding rules
            6. Returns full recovery summary

        If routing_mode == 'static':
            1. Marks link DOWN in physical topology
            2. Leaves flow table unchanged (stale route remains active, causing drops)
            3. Returns unrecovered summary
        """
        self.log_event(
            detection_time,
            "FAILURE_DETECTED",
            f"Controller notified of failure on link ({u}, {v}) at t={detection_time:.2f}",
        )

        # Update physical topology status
        self.topology_manager.set_link_status(u, v, "DOWN")
        self.log_event(detection_time, "TOPOLOGY_UPDATED", f"Link ({u}, {v}) set to DOWN in topology graph.")

        recovery_summary: Dict[str, Any] = {
            "failed_link": (u, v),
            "detection_time": detection_time,
            "affected_flows": [],
            "status": "UNRECOVERED",
            "old_routes": {},
            "new_routes": {},
            "reroute_time": None,
        }

        # Check all installed flows
        for (src, dst), route in list(self.flow_table.items()):
            if self.is_route_affected_by_failure(route, u, v):
                recovery_summary["affected_flows"].append((src, dst))
                recovery_summary["old_routes"][(src, dst)] = list(route)
                old_path_str = " -> ".join(route)

                self.log_event(
                    detection_time,
                    "ROUTE_INVALIDATED",
                    f"Route for [{src}->{dst}] invalidated: {old_path_str}",
                )

                if self.routing_mode == "self_healing":
                    # Recompute alternate path on active subgraph
                    active_graph = self.topology_manager.get_active_graph()
                    try:
                        reroute_time = round(detection_time + self.controller_computation_delay, 3)
                        new_route = self.router.calculate_route(active_graph, src, dst)
                        self.install_route(src, dst, new_route, timestamp=reroute_time)
                        recovery_summary["new_routes"][(src, dst)] = list(new_route)
                        recovery_summary["status"] = "RECOVERED"
                        recovery_summary["reroute_time"] = reroute_time
                        new_path_str = " -> ".join(new_route)
                        self.log_event(
                            reroute_time,
                            "TRAFFIC_REROUTED",
                            f"Alternate path installed for [{src}->{dst}]: {new_path_str}",
                        )
                    except NoPathError:
                        self.log_event(
                            detection_time,
                            "RECOVERY_FAILED",
                            f"No alternate path exists for [{src}->{dst}].",
                        )
                        recovery_summary["status"] = "NO_ALTERNATE_PATH"
                else:
                    # Static mode: do nothing, leave invalid flow entry in place
                    self.log_event(
                        detection_time,
                        "STATIC_MODE_NO_REROUTE",
                        f"Static routing active: No rerouting performed for [{src}->{dst}]. Stale path kept.",
                    )

        return recovery_summary

    def get_flow_table(self) -> Dict[Tuple[str, str], List[str]]:
        """Returns snapshot of current flow table."""
        return {k: list(v) for k, v in self.flow_table.items()}

    def get_event_log(self) -> List[Dict[str, Any]]:
        """Returns full event log."""
        return list(self.event_log)

    def reset(self) -> None:
        """Resets the controller and topology back to baseline clean state."""
        self.flow_table.clear()
        self.event_log.clear()
        self.topology_manager.reset_all_links()
        self.discover_topology()
