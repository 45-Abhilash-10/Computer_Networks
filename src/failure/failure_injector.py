"""
failure_injector.py - Controlled failure injection module for SDN simulation.

Supports scheduling and injecting link failures into the simulated data plane,
recording exact failure timestamps and notifying the simulation environment.
"""

from typing import Tuple, Optional, Dict, Any, List
from src.topology.topology_manager import TopologyManager


class FailureInjector:
    """Manages scheduled fault injection in the simulated network."""

    def __init__(self, topology_manager: TopologyManager):
        self.topology_manager = topology_manager
        self.active_failures: List[Dict[str, Any]] = []

    def inject_link_failure(
        self, u: str, v: str, failure_time: float
    ) -> Dict[str, Any]:
        """
        Immediately disrupts physical connectivity between node u and v.

        Args:
            u: First endpoint of link.
            v: Second endpoint of link.
            failure_time: Simulation timestamp when fault occurs.

        Returns:
            Dict describing failure event.
        """
        # Mark physical link as DOWN
        self.topology_manager.set_link_status(u, v, "DOWN")

        failure_record = {
            "type": "LINK_FAILURE",
            "link": (u, v),
            "failure_time": failure_time,
            "status": "ACTIVE",
        }
        self.active_failures.append(failure_record)
        return failure_record

    def restore_link(self, u: str, v: str) -> None:
        """Restores physical link to UP."""
        self.topology_manager.set_link_status(u, v, "UP")
        self.active_failures = [
            f for f in self.active_failures if f.get("link") != (u, v)
        ]
