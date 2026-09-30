"""
config.py - Centralized configuration parameters for SDN Simulation.

Defines default network topology attributes, simulation parameters,
failure parameters, and file paths.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class SimulationConfig:
    """Configuration settings for SDN discrete-event simulation."""

    # Time & Traffic Settings
    simulation_duration: float = 30.0  # Total discrete simulation time units
    packet_rate: float = 5.0          # Packets generated per simulation time unit
    packet_size_bytes: int = 1024     # Packet payload size in bytes
    random_seed: int = 42             # Seed for deterministic traffic / delays

    # Network Characteristics
    default_bandwidth: float = 100.0  # Mbps
    default_delay: float = 0.5        # Link traversal delay in time units
    default_cost: float = 1.0         # Metric cost for shortest-path calculation

    # Failure & Detection Settings
    failure_time: float = 10.0        # Time unit when scheduled link failure triggers
    failed_link: tuple[str, str] = ("S2", "S3")  # Default link to cut
    heartbeat_interval: float = 1.0   # Polling / heartbeat interval for explicit failure detection

    # Default endpoints for demonstration
    source_host: str = "H1"
    destination_host: str = "H2"

    # Routing Mode: 'self_healing' or 'static'
    routing_mode: str = "self_healing"


# Repository Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RESULTS_DIR = BASE_DIR / "results"
METRICS_DIR = RESULTS_DIR / "metrics"
FIGURES_DIR = RESULTS_DIR / "figures"
DOCS_DIR = BASE_DIR / "docs"

# Ensure output directories exist
METRICS_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
