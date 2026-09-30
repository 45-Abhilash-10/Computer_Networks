"""
recovery_engine.py - Autonomous Recovery / Self-Healing Engine.

Orchestrates the closed-loop recovery process:
1. Coordinates failure detection
2. Invalidates affected routing paths
3. Requests alternate path computation from Dijkstra router
4. Installs alternate flow rules into controller
5. Computes detection delay, reroute delay, and total recovery time
"""

from typing import Dict, List, Optional, Tuple, Any
from src.controller.sdn_controller import SDNController
from src.topology.topology_manager import TopologyManager


class RecoveryEngine:
    """Manages the self-healing lifecycle and calculates recovery time benchmarks."""

    def __init__(self, controller: SDNController, topology_manager: TopologyManager):
        self.controller = controller
        self.topology_manager = topology_manager
        self.recovery_history: List[Dict[str, Any]] = []

    def trigger_recovery(
        self,
        failed_u: str,
        failed_v: str,
        failure_time: float,
        detection_time: float,
    ) -> Dict[str, Any]:
        """
        Executes self-healing response to a detected link failure.

        Args:
            failed_u: First endpoint of failed link.
            failed_v: Second endpoint of failed link.
            failure_time: Inception timestamp of physical failure.
            detection_time: Timestamp when failure was detected by monitoring.

        Returns:
            Dict containing recovery metrics and path transition details.
        """
        # Call controller to handle the failure and perform rerouting
        controller_result = self.controller.handle_failure_notification(
            failed_u, failed_v, detection_time
        )

        reroute_time = controller_result.get("reroute_time")
        detection_delay = max(0.0, detection_time - failure_time)

        if reroute_time is not None:
            reroute_delay = max(0.0, reroute_time - detection_time)
            total_recovery_time = max(0.0, reroute_time - failure_time)
        else:
            reroute_delay = None
            total_recovery_time = None

        record = {
            "failed_link": (failed_u, failed_v),
            "failure_time": round(failure_time, 3),
            "detection_time": round(detection_time, 3),
            "reroute_time": round(reroute_time, 3) if reroute_time is not None else None,
            "detection_delay": round(detection_delay, 3),
            "reroute_delay": round(reroute_delay, 3) if reroute_delay is not None else None,
            "total_recovery_time": round(total_recovery_time, 3) if total_recovery_time is not None else None,
            "status": controller_result.get("status", "UNRECOVERED"),
            "old_routes": controller_result.get("old_routes", {}),
            "new_routes": controller_result.get("new_routes", {}),
            "affected_flows": controller_result.get("affected_flows", []),
        }

        self.recovery_history.append(record)
        return record

    def get_latest_recovery(self) -> Optional[Dict[str, Any]]:
        """Returns the most recent recovery event record."""
        return self.recovery_history[-1] if self.recovery_history else None
