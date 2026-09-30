"""
packet.py - Packet abstraction for discrete-event SDN traffic simulation.

Tracks packet identity, payload metadata, routing path, transit state,
timestamps, and delivery/drop metrics.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class PacketStatus(str, Enum):
    """Lifecycle states of a simulated packet."""
    GENERATED = "GENERATED"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    DROPPED = "DROPPED"
    REROUTED = "REROUTED"


@dataclass
class Packet:
    """Represents a simulated packet traveling through the SDN data plane."""

    packet_id: int
    source: str
    destination: str
    creation_time: float
    size_bytes: int = 1024
    route: List[str] = field(default_factory=list)
    current_node: Optional[str] = None
    delivery_time: Optional[float] = None
    status: PacketStatus = PacketStatus.GENERATED
    drop_reason: Optional[str] = None
    delay: Optional[float] = None
    is_rerouted: bool = False

    def mark_in_transit(self, initial_node: str, route: List[str]) -> None:
        """Transitions packet to IN_TRANSIT with its assigned forwarding route."""
        self.status = PacketStatus.IN_TRANSIT
        self.current_node = initial_node
        self.route = list(route)

    def mark_delivered(self, delivery_time: float) -> None:
        """Marks packet as successfully delivered and records latency."""
        self.delivery_time = delivery_time
        self.delay = round(delivery_time - self.creation_time, 4)
        if self.is_rerouted:
            self.status = PacketStatus.REROUTED
        else:
            self.status = PacketStatus.DELIVERED

    def mark_dropped(self, current_node: str, reason: str) -> None:
        """Marks packet as dropped due to link failure or buffer exhaustion."""
        self.status = PacketStatus.DROPPED
        self.current_node = current_node
        self.drop_reason = reason
        self.delay = None

    def to_dict(self) -> dict:
        """Serializes packet records for pandas dataframe conversion."""
        return {
            "packet_id": self.packet_id,
            "source": self.source,
            "destination": self.destination,
            "creation_time": round(self.creation_time, 3),
            "delivery_time": round(self.delivery_time, 3) if self.delivery_time is not None else None,
            "status": self.status.value,
            "delay": self.delay,
            "route": " -> ".join(self.route) if self.route else "",
            "drop_reason": self.drop_reason or "N/A",
            "is_rerouted": self.is_rerouted,
        }
