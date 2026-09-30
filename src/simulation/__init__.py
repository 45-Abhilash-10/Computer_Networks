"""
simulation module - Packet models and SimPy discrete-event traffic engine.
"""

from src.simulation.packet import Packet, PacketStatus
from src.simulation.traffic_simulator import TrafficSimulator, SimulationResult

__all__ = ["Packet", "PacketStatus", "TrafficSimulator", "SimulationResult"]
