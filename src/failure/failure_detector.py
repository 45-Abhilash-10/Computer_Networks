"""
failure_detector.py - Explicit failure detection via heartbeat/health monitoring.

Simulates periodic switch telemetry polling or echo requests. Quantifies the
detection delay between physical failure inception and controller notification.
"""

from typing import Dict, List, Optional, Tuple, Any
import math
from src.controller.sdn_controller import SDNController
from src.topology.topology_manager import TopologyManager


class FailureDetector:
    """
    Heartbeat and telemetry monitoring service.

    Periodically checks link health across the network data plane.
    When a link heartbeat times out, explicitly notifies the SDN Controller.
    """

    def __init__(
        self,
        controller: SDNController,
        topology_manager: TopologyManager,
        heartbeat_interval: float = 1.0,
    ):
        """
        Args:
            controller: Target SDN Controller to notify on detected failures.
            topology_manager: TopologyManager providing ground-truth link health.
            heartbeat_interval: Time units between periodic health checks.
        """
        self.controller = controller
        self.topology_manager = topology_manager
        self.heartbeat_interval = max(0.1, heartbeat_interval)

        # Track previously detected and notified failed links
        self.detected_failures: Dict[Tuple[str, str], float] = {}
        self.detection_records: List[Dict[str, Any]] = []

    def check_for_failures(
        self, current_time: float, known_failures: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Scans all links for failures during a heartbeat inspection cycle.
        If a newly failed link is found, records detection time and notifies controller.

        Args:
            current_time: Current simulation timestamp.
            known_failures: Optional list of injected failure metadata.

        Returns:
            List of newly detected failure events.
        """
        newly_detected = []

        for u, v, data in self.topology_manager.get_all_links():
            status = data.get("status", "UP")
            pair = tuple(sorted((u, v)))

            # A heartbeat timeout requires waiting at least one heartbeat interval
            # from the failure event to confirm link unresponsiveness
            failure_time = current_time
            if known_failures:
                for f in known_failures:
                    f_link = tuple(sorted(f.get("link", ())))
                    if f_link == pair:
                        failure_time = f.get("failure_time", current_time)
                        break

            # Only detect once the heartbeat timeout has elapsed (strictly > failure_time)
            if status == "DOWN" and pair not in self.detected_failures:
                if current_time < failure_time + self.heartbeat_interval:
                    continue  # Heartbeat probe hasn't timed out yet

                detection_time = current_time
                detection_delay = max(0.0, detection_time - failure_time)

                record = {
                    "link": (u, v),
                    "failure_time": failure_time,
                    "detection_time": detection_time,
                    "detection_delay": round(detection_delay, 3),
                }

                self.detected_failures[pair] = detection_time
                self.detection_records.append(record)
                newly_detected.append(record)

        return newly_detected
